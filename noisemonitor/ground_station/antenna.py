import math


def _set_default(x, data_type, default_value):
    return default_value if x is None else data_type(x)


def wavelength(frequency: float) -> float:
    """
    This function converts a frequency in Hertz into its corresponding wavelength in meter
    :param frequency: The frequency in Hertz
    :return: The wavelength in meter
    """
    if frequency <= 0:
        return float("inf")
    return 300 / (frequency / 1e6)


def opening_angle(frequency: float, diameter_m: float) -> float:
    """
    This function calculates the opening angle / HPBW of a given parabolic antenna.
    Calculated according to https://de.wikipedia.org/wiki/Parabolantenne#Technische_Daten
    :param frequency: The frequency in Hertz
    :param diameter_m: The reflector diameter in meter
    :return: The opening angle / HPBW in degree
    """
    if diameter_m <= 0:
        raise Exception("Diameter of parabolic antenna has to be greater than zero!")
    return 58.8 * wavelength(frequency) / diameter_m


def antenna_gain(frequency: float, diameter_m: float, efficiency: float = 1):
    """
    This function calculates the theoretical gain of a given parabolic antenna.
    Calculated according to https://de.wikipedia.org/wiki/Parabolantenne#Technische_Daten
    :param frequency: The frequency in Hertz
    :param diameter_m: The reflector diameter in meter
    :param efficiency: The aperture efficiency of the reflector
    :return: The theoretical gain of the parabolic reflector in dB
    """
    lin_gain = (math.pi * diameter_m / wavelength(frequency)) ** 2 * efficiency
    db_gain = 10.0 * math.log(lin_gain, 10)
    return db_gain


class GenericAntenna:
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
        """
        This function initializes an generic antenna class.
        :param name: Name of the antenna
        :param frequency_start: Lowest frequency the antenna supports within its bandwidth in Hertz
        :param frequency_stop: Highest frequency the antenna supports within its bandwidth in Hertz
        :param gain: The gain of the antenna in dB
        :param opening_angle_az: The HPBW opening angle in azimuth direction in dB
        :param opening_angle_el: The HPBW opening angle in elevation direction in dB
        """
        self.name = _set_default(name, str, "")
        self.gain = _set_default(gain, float, 0.0)
        self.opening_angle_az = _set_default(opening_angle_az, float, 180.0)
        self.opening_angle_el = _set_default(opening_angle_el, float, 180.0)
        self.frequency_start = _set_default(frequency_start, float, 0.0)
        self.frequency_stop = _set_default(frequency_stop, float, 0.0)

    @property
    def opening_angle(self) -> (float, float):
        """
        This function returns the HPBW opening angle in azimuth and elevation direction.
        :return: HPBW opening angle in azimuth and elevation direction in degree
        """
        return self.opening_angle_az, self.opening_angle_el

    @property
    def center_frequency(self) -> float:
        """
        This function returns the center frequency of the bandwidth of the antenna.
        :return: Center frequency of the bandwidth of the antenna in Hertz
        """
        return (self.frequency_start + self.frequency_stop) / 2

    @property
    def bandwidth(self) -> float:
        """
        This function returns the bandwidth of the antenna.
        :return: Bandwidth of the antenna in Hertz
        """
        return abs(self.frequency_stop - self.frequency_start)

    @property
    def frequency_range(self) -> (float, float):
        """
        This function returns the bandwidth of the antenna as start and stop frequency.
        :return: Start and stop frequency of the antenna in Hertz
        """
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
        """
        This function initializes parapolic type antennas.
        :param name: Name of the antenna
        :param frequency_start: Lowest frequency the antenna supports within its bandwidth in Hertz
        :param frequency_stop: Highest frequency the antenna supports within its bandwidth in Hertz
        :param feed_gain: The gain of the feed antenna of the system in dB
        :param diameter: The reflector diameter in meter
        :param reflector_efficiency: The aperture efficiency of the reflector from 0 to 1
        :param override_gain: Overrides the gain of the parabolic antenna by this value in dB
        """
        super().__init__(
            name=name, frequency_start=frequency_start, frequency_stop=frequency_stop
        )
        self.diameter = _set_default(diameter, float, 1)
        self.reflector_efficiency = _set_default(reflector_efficiency, float, 1)
        self.feed_gain = _set_default(feed_gain, float, 0)
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
