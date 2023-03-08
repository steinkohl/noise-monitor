#! python3

import time
import argparse
import pandas as pd

from noisemonitor import GroundStationController, display_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str)
    parser.add_argument("-tp_az", "--target_position_azimuth", type=float, default=None)
    parser.add_argument(
        "-tp_el", "--target_position_elevation", type=float, default=None
    )
    parser.add_argument("-s_az", "--step_azimuth", type=float, default=None)
    parser.add_argument("-s_el", "--step_elevation", type=float, default=None)
    parser.add_argument("-w_az", "--width_azimuth", type=float, default=None)
    parser.add_argument("-w_el", "--width_elevation", type=float, default=None)
    parser.add_argument("-img", "--take_images", action="store_true")
    parser.add_argument("-res", "--show_results", action="store_true")
    parser.add_argument("-st", "--start_time", type=str, default=None)
    args = parser.parse_args()

    if args.start_time is not None:
        t = pd.to_datetime(args.start_time, utc=True).timestamp()
        while time.time() < t:
            print(f"Time to wait: {int(t-time.time())}sec until {args.start_time} UTC")
            time.sleep(30)

    t_start = int(time.time())
    mission_control = GroundStationController(config_file=args.config_file)

    if (
        args.target_position_azimuth is not None
        and args.target_position_elevation is not None
    ):
        mission_control.set_target_position(
            azimuth=args.target_position_azimuth,
            elevation=args.target_position_elevation,
        )
    else:
        mission_control.set_target_position_to_astro_object()

    if args.step_azimuth is not None or args.step_elevation is not None:
        mission_control.set_step_size(args.step_azimuth, args.step_elevation)

    if args.width_azimuth is not None and args.width_elevation is not None:
        mission_control.set_scan_width(args.width_azimuth, args.width_elevation)

    mission_control.compute_path()
    mission_control.track_motion_path(take_images=args.take_images)

    df = mission_control.get_measurement_points_as_dataframe()
    df.to_csv(f"sweep_data_{t_start}-{int(time.time())}.csv")

    if args.show_results:
        display_results(mission_control)
