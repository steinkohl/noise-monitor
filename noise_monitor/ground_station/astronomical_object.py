from __future__ import annotations

import azely
import pandas as pd
import time

from .data_structures import Position


class AstroObject:
    object_name: str
    observation_location: str
    object_path: pd.DataFrame

    def __init__(self, object_name: str, observation_location: str):
        self.object_name = str(object_name)
        self.observation_location = str(observation_location)
        self.object_path = self._get_object_path()

    def get_position(self, time_point: float = time.time()) -> Position:
        t = time.time()
        if time_point is not None:
            t = float(time_point)
        past_df = self.object_path[self.object_path["timestamp"] <= t]
        if past_df.shape[0] < 1:
            self.object_path = self._get_object_path(timestamp=time_point)
            past_df = self.object_path[self.object_path["timestamp"] <= t]
        past = past_df.iloc[-1]
        future_df = self.object_path[self.object_path["timestamp"] > t]
        if future_df.shape[0] < 1:
            # next day -> get new object path
            self.object_path = self._get_object_path(timestamp=time_point)
            future_df = self.object_path[self.object_path["timestamp"] > t]
        future = future_df.iloc[0]
        return self._interpolate_position(t, past, future)

    @staticmethod
    def _interpolate_position(
        time_now: float, past: pd.Series, future: pd.Series
    ) -> Position:
        # only linear interpolation
        t_diff = future.timestamp - past.timestamp
        t_offset = time_now - past.timestamp
        az_per_sec = (future.az - past.az) / t_diff
        el_per_sec = (future.el - past.el) / t_diff
        az_offset = az_per_sec * t_offset
        el_offset = el_per_sec * t_offset
        az = past.az + az_offset
        el = past.el + el_offset
        return Position(az, el)

    def _get_object_path(self, timestamp: float = time.time()) -> pd.DataFrame:
        # get object path for location for the current day, in UTC and in a frequency of 1min
        df = pd.DataFrame(
            azely.compute(
                self.object_name,
                site=self.observation_location,
                time=str(pd.to_datetime(timestamp, unit="s")),
                view="UTC",
                freq="1T",
            )
        )
        df["timestamp"] = df.index
        df["timestamp"] = df["timestamp"].apply(lambda x: x.value // 1e9)
        df = df.sort_values(by="timestamp")
        return df


if __name__ == "__main__":
    object_name = "sun"
    location = "Technische Universität Berlin"
    obj = AstroObject(object_name=object_name, observation_location=location)
    pos = obj.get_position()
    print(
        f"Current {obj.object_name[0].upper()}{obj.object_name[1:]}-Position: "
        f"Azimuth: {pos.azimuth:.2f}deg, "
        f"Elevation: {pos.elevation:.2f}deg"
    )
