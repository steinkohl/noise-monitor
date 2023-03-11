from __future__ import annotations

from .data_structures import Position, MeasurementPoint
from .sdr import SDR
from .rotator import Rotator
from .antenna import GenericAntenna, ParabolicAntenna
from .webcam import Webcam
from .config_parser import load_config_from_file


class GroundStation:
    location: str
    name: str
    antenna: GenericAntenna = None
    sdr: SDR = None
    rotator: Rotator = None
    webcam: Webcam = None
    config: dict = None

    def __init__(
        self,
        location: str = None,
        name: str = None,
        config_file: str = None,
        config_dict: dict = None,
        no_sdr: bool = False,
        inactive: bool = False,
    ):
        self.location = "" if location is None else str(location)
        self.name = "" if name is None else str(name)
        if config_file is not None:
            self.load_config(config_file, no_sdr=no_sdr, inactive=inactive)
        if config_dict is not None:
            self.config = config_dict
            self._load_config_dict(no_sdr=no_sdr, inactive=inactive)

    def load_config(
        self, config_file: str, no_sdr: bool = False, inactive: bool = False
    ):
        print("Loading ground station config..")
        self.config = load_config_from_file(config_file=config_file)
        self._load_config_dict(no_sdr=no_sdr, inactive=inactive)

    def _load_config_dict(self, no_sdr: bool = False, inactive: bool = False):
        loc = self.config.get("groundstation").get("location")
        self.location = self.location if loc is None else str(loc)
        name = self.config.get("groundstation").get("name")
        self.name = self if name is None else str(name)

        an = self.config.get("groundstation").get("antenna")
        print("Setup Antenna..")
        an_type = an.get("type")
        f_range = an.get("frequency_range")
        try:
            f_start = float(f_range[0])
            f_stop = float(f_range[1])
        except Exception:
            raise Exception(
                "Expected 'frequency_range' to contain two float values! E.g. [430e6, 440e6]"
            )
        self.setup_antenna(
            antenna_type=an_type,
            name=an.get("name"),
            frequency_start=f_start,
            frequency_stop=f_stop,
            feed_gain=an.get("gain") if an_type == "parabolic" else None,
            gain=an.get("gain") if an_type == "generic" else None,
            diameter=an.get("diameter"),
            reflector_efficiency=an.get("reflector_efficiency"),
            override_gain=an.get("override_gain"),
            opening_angle_az=an.get("opening_azimuth"),
            opening_angle_el=an.get("opening_elevation"),
        )
        if not inactive:
            rot = self.config.get("groundstation").get("rotator")
            print("Setup Rotator..")
            self.setup_rotator(
                rotator_type=rot.get("type"),
                rotator_ip=rot.get("netrotctl_ip"),
                rotator_port=rot.get("netrotctl_port"),
                rotator_tolerance=rot.get("positioning_tolerance"),
            )

        if not no_sdr and not inactive:
            sdr = self.config.get("groundstation").get("sdr")
            print("Setup SDR..")
            self.setup_sdr(
                sampling_rate=sdr.get("sampling_rate"),
                device_driver=sdr.get("type"),
                lna_gain=sdr.get("lna_gain"),
                psd_bins=sdr.get("psd_bins"),
            )

        cam = self.config.get("groundstation").get("webcam")
        if cam.get("rtsp_url") is not None:
            print("Setup Webcam..")
            self.webcam = Webcam(
                rtsp_url=cam.get("rtsp_url"),
                cam_opening=cam.get("cam_opening"),
                position_azimuth=cam.get("position_azimuth"),
                position_elevation=cam.get("position_elevation"),
            )

    def setup_sdr(
        self,
        sampling_rate: float = None,
        device_driver: str = None,
        lna_gain: float = None,
        psd_bins: int = None,
    ):
        self.sdr = SDR(
            sampling_rate=sampling_rate,
            device_driver=device_driver,
            lna_gain=lna_gain,
            psd_bins=psd_bins,
        )
        return self

    def setup_antenna(
        self,
        antenna_type: str,
        name: str = None,
        frequency_start: float = None,
        frequency_stop: float = None,
        feed_gain: float = None,
        gain: float = None,
        diameter: float = None,
        reflector_efficiency: float = None,
        override_gain: float = None,
        opening_angle_az: float = None,
        opening_angle_el: float = None,
    ):
        if antenna_type == "generic":
            self.antenna = GenericAntenna(
                name=name,
                frequency_start=frequency_start,
                frequency_stop=frequency_stop,
                gain=gain,
                opening_angle_az=opening_angle_az,
                opening_angle_el=opening_angle_el,
            )
        elif antenna_type == "parabolic":
            self.antenna = ParabolicAntenna(
                name=name,
                frequency_start=frequency_start,
                frequency_stop=frequency_stop,
                feed_gain=feed_gain,
                diameter=diameter,
                reflector_efficiency=reflector_efficiency,
                override_gain=override_gain,
            )
        else:
            raise Exception(
                f"Antennas of type {antenna_type} are currently not supported!"
            )
        return self

    def setup_rotator(
        self,
        rotator_type: str,
        rotator_ip: str = None,
        rotator_port: int = None,
        rotator_tolerance: float = None,
    ):
        if rotator_ip is None or rotator_port is None:
            self.rotator = Rotator(
                rotator_type=rotator_type, positioning_tolerance=rotator_tolerance
            )
        else:
            self.rotator = Rotator(
                rotator_type=rotator_type,
                netrotctl_ip=rotator_ip,
                netrotctl_port=rotator_port,
                positioning_tolerance=rotator_tolerance,
            )
        return self

    def measure_at_position(self, position: Position) -> MeasurementPoint:
        mp = MeasurementPoint(
            target_position=position,
            measurement_position=self.rotator.move_rotator_to_position(position),
            psd_levels=self.sdr.get_psd_levels(),
        )
        return mp


if __name__ == "__main__":
    gs = GroundStation()
    gs.load_config(
        "/home/felix/git/ba-steinkohl/code/noise_monitor/config/gs-config.yaml"
    )
