import math


def set_default(x, data_type, default_value):
    return default_value if x is None else data_type(x)


def wavelength(frequency: float) -> float:
    if frequency <= 0:
        return float("inf")
    return 300 / (frequency / 1e6)


def opening_angle(frequency: float, diameter_m: float) -> float:
    # https://de.wikipedia.org/wiki/Parabolantenne#Technische_Daten
    if diameter_m <= 0:
        raise Exception("Diameter of parabolic antenna has to be greater than zero!")
    return 58.8 * wavelength(frequency) / diameter_m


def antenna_gain(frequency: float, diameter_m: float, efficiency: float = 1):
    # https://de.wikipedia.org/wiki/Parabolantenne#Technische_Daten
    lin_gain = (math.pi * diameter_m / wavelength(frequency)) ** 2 * efficiency
    db_gain = 10.0 * math.log(lin_gain, 10)
    return db_gain


class GenericAntenna:
    """
    Generic antenna class
    """

    name: str
    gain: float
    opening_angle_az: float
    opening_angle_el: float
    frequency_start: float
    frequency_stop: float

    def __init__(
        self,
        name: str = None,
        frequency_start: float = None,
        frequency_stop: float = None,
        gain: float = None,
        opening_angle_az: float = None,
        opening_angle_el: float = None,
    ):
        self.name = set_default(name, str, "")
        self.gain = set_default(gain, float, 0.0)
        self.opening_angle_az = set_default(opening_angle_az, float, 180.0)
        self.opening_angle_el = set_default(opening_angle_el, float, 180.0)
        self.frequency_start = set_default(frequency_start, float, 0.0)
        self.frequency_stop = set_default(frequency_stop, float, 0.0)

    @property
    def opening_angle(self) -> (float, float):
        return self.opening_angle_az, self.opening_angle_el

    @property
    def center_frequency(self) -> float:
        return (self.frequency_start + self.frequency_stop) / 2

    @property
    def bandwidth(self) -> float:
        return abs(self.frequency_stop - self.frequency_start)

    @property
    def frequency_range(self) -> (float, float):
        return self.frequency_start, self.frequency_stop


class ParabolicAntenna(GenericAntenna):
    def __init__(
        self,
        name: str = None,
        frequency_start: float = None,
        frequency_stop: float = None,
        feed_gain: float = None,
        diameter: float = None,
        reflector_efficiency: float = None,
        override_gain: float = None,
    ):
        super().__init__(
            name=name, frequency_start=frequency_start, frequency_stop=frequency_stop
        )
        self.diameter = set_default(diameter, float, 1)
        self.reflector_efficiency = set_default(reflector_efficiency, float, 1)
        self.feed_gain = set_default(feed_gain, float, 0)
        self.dish_gain = 0.0
        if override_gain is not None:
            self.gain = float(override_gain)
        else:
            self.dish_gain = antenna_gain(
                self.center_frequency, self.diameter, self.reflector_efficiency
            )
            self.gain = self.feed_gain + self.dish_gain
        opening = opening_angle(self.center_frequency, self.diameter)
        self.opening_angle_az = opening
        self.opening_angle_el = opening
