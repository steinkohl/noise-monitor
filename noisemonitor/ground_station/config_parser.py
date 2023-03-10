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
    This function loads the given yaml config file and adds default values, if settings are omitted.
    :param config_file: Path of the yaml file, containing the ground station config
    :param default_values: Dict with default settings
    :return: updated dict, with all necessary setting parameters
    """
    vals = default_values.copy()
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        gs = config.get("groundstation")
        con = config.get("controller")
        if gs is None:
            print("No groundstation given in config file -> Fallback to defaults")
        else:
            # only update values which are not None
            for k_o, v_o in gs.items():
                if v_o is not None:
                    if isinstance(v_o, dict):
                        for k, v in v_o.items():
                            if v is not None:
                                vals["groundstation"][k_o][k] = v
                    else:
                        vals["groundstation"][k_o] = gs[k_o]
        if con is None:
            print("No controller given in config file -> Fallback to defaults")
            config.update("controller", config.get("controller"))
        else:
            # only update values which are not None
            for k, v in con.items():
                if v is not None:
                    vals["controller"][k] = v
    except Exception as e:
        raise Exception(f"Could not parse {config_file} due to Error: {e}")
    return vals

