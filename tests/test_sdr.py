import random
import time

from code.noise_monitor.noise_monitor.ground_station import GenericSDR


class MockSDR(GenericSDR):
    data_start: int
    data_stop: int
    dummy_data: list

    def __init__(self):
        random.seed(42)  # FIXME: For debugging only!
        super().__init__(1250e6, 2048e3, "mock")
        self.data_start = 45
        self.data_stop = 242
        with open("soapypower_stdout.txt", "r") as f:
            self.dummy_data = f.readlines()
        super(MockSDR, self)._find_frequency_pos(self.dummy_data[self.data_start])

    def start_rx(self) -> None:
        return

    def stop_rx(self) -> None:
        return

    def get_power_level(self) -> float:
        idx = random.randint(self.data_start, self.data_stop)
        line = self.dummy_data[idx]
        # delay function to simulate real interaction
        time.sleep(random.random() / 3)
        return super(MockSDR, self)._parse_power_line(line)
