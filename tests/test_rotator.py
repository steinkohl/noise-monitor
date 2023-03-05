import random


class MockRotator(GenericRotator):
    debug: bool = False
    _get_counter: int = 0
    _azimuth_position: float = 0.0
    _elevation_position: float = 0.0
    _azimuth_target: float = 0.0
    _elevation_target: float = 0.0
    _positioning_tolerance: float = 0.1

    def __init__(self, positioning_tolerance: float = 0.1, debug_mode: bool = True):
        super(MockRotator, self).__init__(positioning_tolerance)
        self.debug = bool(debug_mode)

    def get_position(self) -> Position:
        self._get_counter += 1
        # fake motion
        self._azimuth_position += (self._azimuth_target - self.azimuth_position) / 3
        self._elevation_position += (
            self._elevation_target - self.elevation_position
        ) / 3
        az, el = self._azimuth_position, self._elevation_position
        err = random.random() / self._get_counter
        err_az = az + err if random.random() < 0.5 else az - err
        err_el = el + err if random.random() < 0.5 else el - err
        self._azimuth_position = err_az
        self._elevation_position = err_el
        if self.debug is True:
            print(f"Rotator position: AZ{err_az:.2f}, EL{err_el:.2f}")
        return err_az, err_el

    def set_position(self, azimuth: float, elevation: float):
        super(MockRotator, self).set_position(azimuth, elevation)
        self._get_counter = 0


if __name__ == "__main__":
    rotator = Rotator(rotator_type="mock", debug_mode=True)
    rotator.move_rotator_to_position(Position(90, 10))
