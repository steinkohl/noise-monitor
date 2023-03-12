import cv2
import numpy as np

from .antenna import GenericAntenna
from .data_structures import Position


class Webcam:
    rtsp_url: str
    cam_opening: float
    position_azimuth: float
    position_elevation: float

    def __init__(
        self,
        rtsp_url: str,
        cam_opening: float,
        position_azimuth: float,
        position_elevation: float,
    ):
        """
        This function initializes the webcam.
        :param rtsp_url: The RTSP url of the webcam.
        :param cam_opening: The horizontal opening angle of the camera lens in degree
        :param position_azimuth: The relative azimuth position of the antenna's pointing vector in the image from 0 to 1
        :param position_elevation: The relative elevation position of the antenna's pointing vector in the image from 0 to 1
        """
        self.rtsp_url = str(rtsp_url)
        self.cam_opening = float(cam_opening)
        self.position_azimuth = float(position_azimuth)
        self.position_elevation = float(position_elevation)

    def take_image(
        self, image_path: str, overlay: bool = True, antenna: GenericAntenna = None
    ):
        """
        This function takes an images with the webcam and saves the file.
        :param image_path: File path where the image should be stored
        :param overlay: Shall the image contain the overlay of the ground station information - True or False
        :param antenna: The antenna object necessary for the overlay
        :return: None
        """
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        _, img = cap.read()
        if overlay:
            img = self.create_overlay(img, antenna)
        cv2.imwrite(image_path, img)
        cap.release()
        return

    def create_overlay(
        self,
        img: np.ndarray,
        antenna: GenericAntenna,
        rotator_position: Position = None,
        object_name: str = None,
        object_position: Position = None,
    ) -> np.ndarray:
        """
        This function creates an image overlay based on the information of the antenna object.
        :param img: Image which shall be augmented with the overlay
        :param antenna: The antenna object, containing the data for the overlay
        :param rotator_position: The position of the rotator which shall be annotated onto the image
        :param object_name: The name of the object which is projected into the overlay, e.g. "Sun"
        :param object_position: The position of the object which is projected into the overlay
        :return:
        """
        red_color = (0, 0, 255)
        green_color = (0, 255, 0)
        blue_color = (255, 0, 0)
        line_hight_px = 55
        thickness = 2

        # add cross
        w = img.shape[1]
        h = img.shape[0]
        x = int(w * self.position_azimuth)
        y = int(h * self.position_elevation)
        cross_radius = int(w * 0.02)
        cv2.line(
            img, (x, y - cross_radius), (x, y + cross_radius), red_color, thickness
        )
        cv2.line(
            img, (x - cross_radius, y), (x + cross_radius, y), red_color, thickness
        )

        # add opening angle
        az, el = antenna.opening_angle
        r_x = round(w * (az / self.cam_opening) / 2)
        r_y = round(w * (el / self.cam_opening) / 2)
        cv2.ellipse(img, (x, y), (r_x, r_y), 0, 0, 360, green_color, thickness)

        # add description to image
        lines = [
            f"Antenna: {antenna.name}",
            f"Opening Angle: AZ{az:.2f} EL{el:.2f} [deg]",
            f"Frequency Range: {antenna.frequency_range[0]/1e6:.2f}-{antenna.frequency_range[1]/1e6:.2f} [MHz]",
            f"Gain: {antenna.gain:.2f} [dBi]",
            "",
        ]

        if rotator_position is not None:
            lines += [
                f"Rotator Position: AZ{rotator_position.azimuth:.2f} EL{rotator_position.elevation:.2f} [deg]"
            ]

        if object_name is not None and object_position is not None:
            obj_n = f"{str(object_name[0]).upper()}{str(object_name[1:]).lower()}"
            lines += [
                f"{obj_n} Position: AZ{object_position.azimuth:.2f} EL{object_position.elevation:.2f} [deg]"
            ]
            az_diff = object_position.azimuth - rotator_position.azimuth
            el_diff = object_position.elevation - rotator_position.elevation
            if az_diff < 0:
                az_diff += 360
            if az_diff > 180:
                az_diff -= 360
            px_per_deg = w / self.cam_opening
            ox, oy = x + int(px_per_deg * az_diff), y - int(px_per_deg * el_diff)
            cv2.line(
                img,
                (ox, oy - cross_radius),
                (ox, oy + cross_radius),
                blue_color,
                thickness,
            )
            cv2.line(
                img,
                (ox - cross_radius, oy),
                (ox + cross_radius, oy),
                blue_color,
                thickness,
            )
            cv2.putText(
                img,
                obj_n,
                (ox + 10, oy - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                blue_color,
                thickness,
            )

        for i, line in enumerate(lines, start=1):
            cv2.putText(
                img,
                line,
                (10, line_hight_px * i),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                green_color,
                thickness,
            )

        return img


if __name__ == "__main__":
    webcam = Webcam(
        rtsp_url="rtsp://admin:430,200@192.168.59.49:554/h264Preview_01_main",
        cam_opening=90,
        position_azimuth=0.5742,
        position_elevation=0.5625,
    )
    antenna = GenericAntenna(
        name="Test-Antenna",
        frequency_start=430e6,
        frequency_stop=440e6,
        gain=15.8,
        opening_angle_az=36,
        opening_angle_el=18,
    )
    webcam.take_image("cam-overlay.png", antenna=antenna)
