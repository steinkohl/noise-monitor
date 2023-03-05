#! python3

import cv2
import argparse

import noise_monitor

WINDOW_NAME = "Rotator Webcam"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str)
    parser.add_argument("-r", "--rescale_factor", type=float, default=0.5)
    args = parser.parse_args()

    factor = args.rescale_factor
    gsc = noise_monitor.GroundStationController(
        config_file=args.config_file, no_sdr=True
    )

    cap = cv2.VideoCapture(gsc.ground_station.webcam.rtsp_url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("Cannot open RTSP webcam stream")
        exit(-1)

    print("Start Webcam overlay processing..")

    while True:
        _, image = cap.read()

        image = gsc.ground_station.webcam.create_overlay(
            img=image,
            antenna=gsc.ground_station.antenna,
            rotator_position=gsc.ground_station.rotator.get_position(),
            object_name=gsc.astro_object.object_name,
            object_position=gsc.astro_object.get_position(),
        )

        # calculate new size and resize image
        width = int(image.shape[1] * factor)
        height = int(image.shape[0] * factor)
        image = cv2.resize(image, (width, height))

        cv2.imshow(WINDOW_NAME, image)

        # Press ESC or click X to exit
        if (
            cv2.waitKey(1) == 27
            or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1
        ):
            break

    cap.release()
    cv2.destroyAllWindows()
