from __future__ import annotations

import io
import subprocess
import time
import os
import signal
import pandas as pd

from .data_structures import PSDLevels


class SDR:
    _sdr: GenericSDR = None

    def __init__(
        self,
        sampling_rate: float = None,
        device_driver: str = None,
        lna_gain: float = None,
        psd_bins: int = None,
    ):
        if device_driver is None:
            sdrs = self._detect_sdrs()
            if len(sdrs) > 1:
                raise ValueError(
                    f"Expected one SDR but found {len(sdrs)} devices.\n"
                    f"\t-> Please specify device driver!"
                )
            if len(sdrs) < 1:
                raise ValueError("Could not auto detect SDR!")

            # only one sdr found -> set properties
            sdr = sdrs[0]
            device_driver = sdr["driver"]
        if device_driver == "uhd":
            self._sdr = UsrpSDR(
                sampling_rate=sampling_rate, lna_gain=lna_gain, psd_bins=psd_bins
            )
        elif device_driver == "lime":
            self._sdr = LimeSDR(
                sampling_rate=sampling_rate, lna_gain=lna_gain, psd_bins=psd_bins
            )
        elif device_driver == "rtlsdr":
            self._sdr = RtlSDR(
                sampling_rate=sampling_rate, lna_gain=lna_gain, psd_bins=psd_bins
            )
        else:
            raise NotImplementedError(f"No auto setup defined for {device_driver} SDR!")

    def __del__(self):
        self.stop_rx()

    def start_rx(self, frequency: float):
        if self._sdr is not None:
            self._sdr.start_rx(frequency)

    def stop_rx(self):
        if self._sdr is not None:
            self._sdr.stop_rx()

    def get_psd_levels(self) -> PSDLevels:
        return self._sdr.get_psd_levels()

    @property
    def frequency(self) -> float:
        return self._sdr.frequency

    @staticmethod
    def _detect_sdrs() -> list:
        """
        Detects Connected SDRs with feature SoapySDR support, if SoapySDR and drivers are installed.
        """
        proc = subprocess.Popen(
            "python3 -m soapypower --detect", shell=True, stdout=subprocess.PIPE
        )
        sdrs = []
        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            data_segments = line.replace("\n", "").replace(" ", "").split(",")
            # skip info text and audio devices
            device = data_segments[0].lower()
            if device.startswith("driver") and not device.endswith("audio"):
                device_dict = {}
                for data in data_segments:
                    if "=" in data:
                        property_value = data.split("=")
                        device_dict[property_value[0]] = property_value[1]
                sdrs.append(device_dict)
        return sdrs


class GenericSDR:
    sampling_rate: float
    device_driver: str
    frequency: float = None
    lna_gain: float = None
    psd_bins: int = 16
    tune_delay: float = 1
    start_delay: float = 10
    _process: subprocess.Popen = None
    _start_time: float = None
    _start_delay_done: bool = False

    def __init__(
        self,
        sampling_rate: float,
        device_driver: str,
        psd_bins: int = None,
        lna_gain: float = None,
    ):
        self.sampling_rate = float(sampling_rate)
        self.device_driver = str(device_driver)
        if psd_bins is not None:
            self.psd_bins = int(psd_bins)
        if lna_gain is not None:
            self.lna_gain = float(lna_gain)

    def __del__(self):
        self.stop_rx()

    def start_rx(self, frequency: float) -> None:
        self.frequency = float(frequency)
        # compose command string for soapy_power
        command = (
            f"python3 -m soapypower "
            f"--freq {self.frequency} "
            f"--rate {self.sampling_rate} "
            f"--bins {self.psd_bins} "
            f"--tune-delay {self.tune_delay} "
            f"--device 'driver={self.device_driver}' "
            f"--gain {self.lna_gain} "
            f"--time 1 --quiet --continue"
        )  # + f"--bandwidth {56e6}"
        # start background process
        if self._process is not None:
            self.stop_rx()
        self._process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        print("SDR subprocess started successfully.")
        self._start_time = time.time()

    def stop_rx(self) -> None:
        if self._process is not None:
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            print("SDR subprocess terminated.")

    def change_frequency(self, frequency: float):
        print(f"Change SDR frequency to {frequency/1e6:.3f}MHz")
        self.start_rx(frequency=frequency)

    def get_psd_levels(self) -> PSDLevels:
        """
        Get actual power spectral density level.
        Is a blocking function!
        """
        # if start up time delay is not already done
        if not self._start_delay_done:
            self._start_delay_done = True
            time_to_wait = self.start_delay - (time.time() - self._start_time)
            time.sleep(time_to_wait if time_to_wait > 0 else 0)
        data = self._get_current_psd_data()
        psd_levels = PSDLevels(
            timestamp=pd.Timestamp(f"{data[0]} {data[1]}"),  # 0 = date, 1 = time
            frequency_start=float(data[2]),  # 2 = f_start
            frequency_stop=float(data[3]),  # 3 = f_stop
            frequency_step=float(data[4]),  # 4 = f_step
            samples=int(data[5]),  # 5 = samples
            psd_levels=[float(x) for x in data[6:]],  # 6 - x = power levels
        )
        return psd_levels

    def _get_current_psd_data(self) -> [str]:
        self._dump_stdout_buffer()  # get rid of old psd measurements in buffer
        line = self._process.stdout.readline()  # get new / next output
        data = str(line, encoding="utf-8").replace("\n", "").replace(" ", "").split(",")
        return data

    def _dump_stdout_buffer(self) -> None:
        # dump stdout buffer
        duration_s = 0
        # dump every thing until have to wait on new measurement data
        while duration_s < 0.001:
            start_t = time.time()
            _ = self._process.stdout.readline()
            duration_s = time.time() - start_t


class UsrpSDR(GenericSDR):
    def __init__(
        self,
        sampling_rate: float = None,
        lna_gain: float = 76,
        psd_bins: int = None,
    ):
        if sampling_rate is None:
            sampling_rate = 4e6
        super().__init__(
            sampling_rate=sampling_rate,
            device_driver="uhd",
            lna_gain=lna_gain,
            psd_bins=psd_bins,
        )


class LimeSDR(GenericSDR):
    def __init__(
        self,
        sampling_rate: float = None,
        lna_gain: float = None,
        psd_bins: int = None,
    ):
        if sampling_rate is None:
            sampling_rate = 4e6
        super().__init__(
            sampling_rate=sampling_rate,
            device_driver="lime",
            lna_gain=lna_gain,
            psd_bins=psd_bins,
        )


class RtlSDR(GenericSDR):
    def __init__(
        self,
        sampling_rate: float = None,
        lna_gain: float = 37.2,
        psd_bins: int = None,
    ):
        if sampling_rate is None:
            sampling_rate = 2048e3
        super().__init__(
            sampling_rate=sampling_rate,
            device_driver="rtlsdr",
            lna_gain=lna_gain,
            psd_bins=psd_bins,
        )


if __name__ == "__main__":
    sdr = SDR()
    sdr.start_rx(frequency=430e6)
    psds = sdr.get_psd_levels()
    print(f"PDS: {psds.as_dict()}")
