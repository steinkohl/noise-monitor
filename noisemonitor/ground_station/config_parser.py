import yaml


DEFAULT_VALUES = {
    "groundstation": {
        "name": "DK0TU Groundstation",
        "location": "52.5122, 13.3270",
        "rotator": {
            "type": "spid",
            "netrotctl_ip": None,
            "netrotctl_port": None,
            "positioning_tolerance": None,
        },
        "sdr": {
            "type": None,
            "sample_rate": None,
            "lna_gain": None,
            "psd_bins": None,
        },
        "antenna": {
            "name": "Dipole",
            "type": "generic",
            "gain": 2.15,
            "opening_azimuth": 180,
            "opening_elevation": 180,
            "diameter": None,
            "frequency_range": [1240e9, 1250e9],
            "reflector_efficiency": None,
            "override_gain": None,
        },
        "webcam": {
            "rtsp_url": None,
            "cam_opening": None,
            "position_azimuth": None,
            "position_elevation": None,
        },
    },
    "controller": {
        "target_object": "Sun",
        "target_frequency": None,
        "application_port": 8050,
        "application_ip": "127.0.0.1",
        "step_size_azimuth": None,
        "step_size_elevation": None,
        "scan_width_azimuth": 20,
        "scan_width_elevation": 20,
    },
}


def load_config_from_file(
    config_file: str,
    default_values: dict = DEFAULT_VALUES,
) -> dict:
    """
    TODO: Loads config file and returns standardized dictionary
    """
    vals = default_values.copy()
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    if config.get("groundstation") is None:
        print("No groundstation given in config file -> Fallback to defaults")
    if config.get("controller") is None:
        print("No controller given in config file -> Fallback to defaults")
    # only update values which are not None
    vals.update((k, v) for k, v in config.items() if v is not None)
    return vals
