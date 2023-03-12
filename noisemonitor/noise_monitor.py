#! python3

import argparse
import pandas as pd

from noisemonitor import GroundStationController, display_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Displays results of previously captured noise sweep")
    parser.add_argument("config_file", type=str, help="Yaml configuration file of the ground station")
    parser.add_argument("sweep_csv", type=str, help="CSV file, containing the previously recorded noise sweep")
    args = parser.parse_args()

    df = pd.read_csv(args.sweep_csv, index_col=0)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    mission_control = GroundStationController(
        config_file=args.config_file, inactive=True
    )
    display_results(controller=mission_control, sweep_df=df)
