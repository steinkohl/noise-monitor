from __future__ import annotations

import time
import math
import pandas as pd

from .ground_station import GroundStation
from .astronomical_object import AstroObject
from .data_structures import MeasurementPoint, Position
from .config_parser import load_config_from_file


class GroundStationController:
    ground_station: GroundStation = None
    astro_object: AstroObject = None
    motion_path: [Position] = []
    measurement_points: [MeasurementPoint] = []
    step_size: (float, float) = (5, 5)
    target_position: Position = Position(180, 45)
    scan_width: (float, float) = (360, 90)
    target_frequency: float = None
    config: dict = None
    port: int = None
    ip: str = None

    def __init__(
        self,
        config_file: str = None,
        ground_station: GroundStation = None,
        astronomical_object: str = None,
        scan_width: (float, float) = None,
        step_size: (float, float) = None,
        application_port: int = None,
        application_ip: str = None,
        no_sdr: bool = False,
        inactive: bool = False,
    ):
        """
        This function initializes the ground station controller.
        :param config_file: The path of the ground station config file
        :param ground_station: The ground station object which shall be controlled
        :param astronomical_object: The name of the astronomical object which should be tracked
        :param scan_width: The scan width of the sky area with shall be scanned, given in degree (AZ, EL)
        :param step_size: The step size in which the sky area shall be scanned, given in degree (AZ, EL)
        :param application_port: The port of the dash application, where the results shall be presented
        :param application_ip: The IP address of the dash application, where the results shall be presented
        :param no_sdr: If set True, the ground station class will be initialized without an SDR
        :param inactive: If set True, the ground station class will be initialized without an SDR or rotator
        """
        if config_file is not None:
            self.config = load_config_from_file(config_file)
            c = self.config["controller"]
            self.target_frequency = c.get("target_frequency")
            self.port = c.get("application_port")
            self.ip = c.get("application_ip")
            self.set_scan_width(
                c.get("scan_width_azimuth"), c.get("scan_width_elevation")
            )
            self.set_step_size(c.get("step_size_azimuth"), c.get("step_size_elevation"))
            self.ground_station = GroundStation(
                config_dict=self.config, no_sdr=no_sdr, inactive=inactive
            )
            self._load_astro_object()
        if ground_station is not None:
            self.ground_station = ground_station
        if astronomical_object is not None:
            self._load_astro_object(str(astronomical_object))
        if scan_width is not None:
            self.set_scan_width(scan_width[0], scan_width[1])
        if step_size is not None:
            self.set_step_size(step_size[0], step_size[1])
        if application_port is not None:
            self.port = application_port
        if application_ip is not None:
            self.ip = application_ip

    def _load_astro_object(self, object_name: str = None):
        if object_name is None:
            object_name = str(self.config["controller"]["target_object"]).lower()
        print(f"Get {object_name} trajectory..")
        self.astro_object = AstroObject(
            object_name=object_name,
            observation_location=self.ground_station.location,
        )

    def set_target_position(self, azimuth: float, elevation: float):
        """
        This function sets the target position of the measurement
        :param azimuth: Azimuth angle in degree
        :param elevation: Elevation angle in degree
        :return: None
        """
        self.target_position = Position(azimuth, elevation)

    def set_target_position_to_astro_object(self):
        """
        This function sets the target position of the measurement to the defined astronomical object
        :return: None
        """
        self.target_position = self.astro_object.get_position()

    def set_target_frequency(
        self, frequency: float = None, set_center_frequency: bool = False
    ):
        """
        This function sets the target frequency for the measurement.
        :param frequency: The frequency where the PSD measurements shall take place
        :param set_center_frequency: In True and no frequency is provided, the frequency will be set to the center frequency of the antenna
        :return: None
        """
        if frequency is None:
            frequency = self.target_frequency
        if frequency is None or set_center_frequency:
            frequency = self.ground_station.antenna.center_frequency
        self.ground_station.sdr.start_rx(frequency=frequency)

    def set_scan_width(self, azimuth: float, elevation: float):
        """
        This function sets the scan width of the sky area with shall be scanned
        :param azimuth: Scan width in azimuth direction in degree
        :param elevation: Scan width in elevation direction in degree
        :return: None
        """
        self.scan_width = (float(azimuth), float(elevation))

    def set_step_size(self, azimuth: float = None, elevation: float = None):
        """
        This function sets the step size of the sky area with shall be scanned
        :param azimuth: Step size in azimuth direction in degree
        :param elevation: Step size in elevation direction in degree
        :return: None
        """
        if azimuth is None:
            print("Scan width in azimuth will be set to half HPBW")
            azimuth = self.ground_station.antenna.opening_angle_az / 2
        if elevation is None:
            print("Scan width in elevation will be set to half HPBW")
            elevation = self.ground_station.antenna.opening_angle_el / 2
        self.step_size = (float(azimuth), float(elevation))

    def compute_path(self):
        """
        This function calculates the motion path for the noise measurement.
        :return: None

        A -> Start Point
        Z -> End Point
        X -> Center Point
        # -> Path Points

        # - # - # - # - Z
        |
        # - # - # - # - #
                        |
        # - # - X - # - #
        |
        #   # - # - #   #
                        |
        A - # - # - # - #
        """
        if self.step_size is None:
            raise AttributeError(
                "The step_size is not defined for azimuth or elevation!"
            )
        if self.scan_width is None:
            raise AttributeError(
                "The scan_width is not defined for azimuth or elevation!"
            )
        if self.target_position is None:
            raise AttributeError(
                "The target_position is not defined for azimuth or elevation!"
            )

        col_num = math.ceil(self.scan_width[0] / self.step_size[0])
        row_num = math.ceil(self.scan_width[1] / self.step_size[1])

        az_diff = col_num * self.step_size[0] - self.scan_width[0]
        az_offset = (self.scan_width[0] + az_diff) / 2 - self.step_size[0] / 2
        start_az = self.target_position.azimuth - az_offset

        el_diff = row_num * self.step_size[1] - self.scan_width[1]
        el_offset = (self.scan_width[1] + el_diff) / 2 - self.step_size[1] / 2
        start_el = self.target_position.elevation - el_offset

        for row in range(row_num):
            for col in range(col_num):
                col_step = col if row % 2 == 0 else col_num - col - 1
                az = start_az + self.step_size[0] * col_step
                el = start_el + self.step_size[1] * row
                self.motion_path.append((az, el))
        self._limit_axis()

    def track_motion_path(self, take_images: bool = False):
        """
        This function processes all previously computed points on the motion path and takes measurements.
        :param take_images: If set True, an image will be taken at each position
        :return: None
        """
        self.set_target_frequency()
        for az_pos, el_pos in self.motion_path:
            target_pos = Position(az_pos, el_pos)
            try:
                mp = self.ground_station.measure_at_position(target_pos)
            except Exception as e:
                print(
                    f"Could not measure at {target_pos} due to Exception: {e}\n"
                    f"Try resetting rotator motor driver and try again.."
                )
                try:
                    self.ground_station.rotator.reset_motor_driver()
                    mp = self.ground_station.measure_at_position(target_pos)
                except Exception as e:
                    print(
                        f"Could not get rotator to work - Exception: {e}\n"
                        f"Exit motion tracking.."
                    )
                    break
            self.measurement_points.append(mp)
            if take_images:
                file_name = f"tracking_image_{int(mp.timestamp.timestamp())}.png"
                try:
                    self.take_image(file_name)
                except Exception as e:
                    print(
                        f"Could not take image due to Exception: {e}\nRetry taking image.."
                    )
                    try:
                        self.take_image(file_name)
                    except Exception as e:
                        print(
                            f"Could not take image due to Exception: {e}\nSkip imaging for this position.."
                        )
            is_pos = mp.measurement_position
            print(
                f"Measured PSDs at position AZ{is_pos.azimuth:.2f}, EL{is_pos.elevation:.2f}"
            )
        self.ground_station.sdr.stop_rx()

    def track_object(self, duration_s: float = 3600, sleep_interval_s: float = 5):
        """
        This function tracks the astronomical object for the given time frame.
        :param duration_s: The duration of the object tracking in seconds
        :param sleep_interval_s: The interval in which the position shall be updated, in seconds
        :return: None
        """
        stop_t = time.time() + duration_s
        while time.time() < stop_t:
            pos = self.astro_object.get_position()
            print(
                f"Target ({self.astro_object.object_name}) position: "
                f"AZ{pos.azimuth:.2f}, EL{pos.elevation:.2f}"
            )
            self.ground_station.rotator.move_rotator_to_position(pos)
            print(f"Wait {sleep_interval_s:.1f}sec until next position update..")
            time.sleep(sleep_interval_s)

    def _limit_axis(self):
        # limit azimuth to 0-360° and elevation to 0-90°
        points = self.motion_path
        self.motion_path = []
        for az, el in points:
            if el > 90:
                if el > 180:
                    raise Exception(f"Can only handle elevation 0..180° but got{el}°!")
                el -= 90.0
                az = 180.0 - az
            if az < 0:
                az += 360.0
            self.motion_path.append((az, el))

    def take_image(self, image_path: str, overlay: bool = True):
        """
        This function takes an image with the provided webcam.
        :param image_path: The path where the image shall be stored
        :param overlay: If set True, an overlay with additional information will be added to the image
        :return: None
        """
        self.ground_station.webcam.take_image(
            image_path=image_path, overlay=overlay, antenna=self.ground_station.antenna
        )

    def get_measurement_points(self) -> [MeasurementPoint]:
        """
        This function returns the measurement results of the previous noise sweep
        :return: List of MeasurementPoints
        """
        return self.measurement_points

    def get_measurement_points_as_dataframe(self) -> pd.DataFrame:
        """
        This function returns the measurement results of the previous noise sweep, converted as a pandas DataFrame
        :return: DataFrame with measurement results
        """
        return pd.DataFrame([x.as_dict() for x in self.get_measurement_points()])


if __name__ == "__main__":
    config_file = "/home/felix/git/ba-steinkohl/code/noise_monitor/config/l-s-band-dish-remote.yaml"
    mission_control = GroundStationController(config_file=config_file)
    mission_control.compute_path()
    mission_control.track_motion_path()
    df = pd.DataFrame([x.as_dict() for x in mission_control.get_measurement_points()])
    df.to_csv(f"sun_sweep_{int(time.time())}.csv")
    a = 1
