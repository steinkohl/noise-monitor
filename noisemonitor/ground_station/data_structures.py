from dataclasses import dataclass
import pandas as pd


@dataclass
class Position:
    azimuth: float
    elevation: float

    def __add__(self, other):
        return Position(self.azimuth + other.azimuth, self.elevation + other.elevation)

    def __sub__(self, other):
        return Position(self.azimuth - other.azimuth, self.elevation - other.elevation)

    def __abs__(self):
        return Position(abs(self.azimuth), abs(self.elevation))

    def as_dict(self):
        return {
            "azimuth": self.azimuth,
            "elevation": self.elevation,
        }


@dataclass
class PSDLevels:
    timestamp: pd.Timestamp
    frequency_start: float
    frequency_stop: float
    frequency_step: float
    samples: int
    psd_levels: [float]

    def as_dict(self):
        return {
            "timestamp": self.timestamp,
            "frequency_start": self.frequency_start,
            "frequency_stop": self.frequency_stop,
            "frequency_step": self.frequency_step,
            "samples": self.samples,
            **{f"psd_{i}": self.psd_levels[i] for i in range(len(self.psd_levels))},
            "psd_min": min(self.psd_levels),
            "psd_max": max(self.psd_levels),
            "psd_mean": sum(self.psd_levels) / len(self.psd_levels),
        }


@dataclass
class MeasurementPoint:
    target_position: Position
    measurement_position: Position
    center_frequency: float
    psd_bandwidth: float
    psd_levels: PSDLevels
    timestamp: pd.Timestamp

    def __init__(
        self,
        target_position: Position,
        measurement_position: Position,
        psd_levels: PSDLevels,
    ):
        self.target_position = target_position
        self.measurement_position = measurement_position
        self.psd_levels = psd_levels
        self.timestamp = psd_levels.timestamp
        self.psd_bandwidth = psd_levels.frequency_step
        self.center_frequency = (
            psd_levels.frequency_start + psd_levels.frequency_stop
        ) / 2

    def as_dict(self):
        return {
            "target_azimuth": self.target_position.azimuth,
            "target_elevation": self.target_position.elevation,
            "measurement_azimuth": self.measurement_position.azimuth,
            "measurement_elevation": self.measurement_position.elevation,
            "center_frequency": self.center_frequency,
            "psd_bandwidth": self.psd_bandwidth,
            **self.psd_levels.as_dict(),
        }
