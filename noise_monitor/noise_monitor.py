import argparse
import pandas as pd

from ground_station import GroundStationController, display_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str)
    parser.add_argument("sweep_csv", type=str)
    args = parser.parse_args()

    df = pd.read_csv(args.sweep_csv, index_col=0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    mission_control = GroundStationController(config_file=args.config_file, inactive=True)
    display_results(controller=mission_control, sweep_df=df)
