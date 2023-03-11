import pandas as pd
import plotly.graph_objects as go

from ..ground_station import GroundStationController, Position
from .gauss_fit_2d import gaussian_fit_2d_mesh, gaussian_fit_2d_max_pos


def create_3d_figure(sweep_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    bandwidth = sweep_df["psd_bandwidth"].unique()
    if bandwidth.size > 1:
        raise Exception(
            f"Expected only one resolution bandwidth within the same sweep file, but got {bandwidth}"
        )
    bandwidth = bandwidth[0]

    X, Y, Z = gaussian_fit_2d_mesh(
        x=sweep_df["measurement_azimuth"],
        y=sweep_df["measurement_elevation"],
        z=sweep_df[f"psd_min"],
    )
    fig.add_trace(
        go.Surface(
            x=X, y=Y, z=Z,
            opacity=0.5, name="Gauss_Fit",
            showscale=False,
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=sweep_df["measurement_azimuth"],
            y=sweep_df["measurement_elevation"],
            z=sweep_df[f"psd_min"],
            opacity=0.9,
            name="PSD_Min",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=sweep_df["measurement_azimuth"],
            y=sweep_df["measurement_elevation"],
            z=sweep_df[f"psd_mean"],
            opacity=0.9,
            name="PSD_Mean",
            visible="legendonly",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=sweep_df["measurement_azimuth"],
            y=sweep_df["measurement_elevation"],
            z=sweep_df[f"psd_max"],
            opacity=0.9,
            name="PSD_Max",
            visible="legendonly",
        )
    )
    psd_bins = (
        sum([1 if "psd" in n else 0 for n in sweep_df.columns]) - 4
    )  # -(min, mean, max, bandwidth)
    for i in range(psd_bins):
        fig.add_trace(
            go.Scatter3d(
                x=sweep_df["measurement_azimuth"],
                y=sweep_df["measurement_elevation"],
                z=sweep_df[f"psd_{i}"],
                opacity=0.5,
                name=f"PSD_Bin_{i}",
                visible="legendonly",
            )
        )
    fig.update_layout(
        legend_title_text="PSD Levels",
        scene=dict(
            xaxis_title="Azimuth [°]",
            yaxis_title="Elevation [°]",
            zaxis_title=f"PSD [dBFS/{int(bandwidth/1000)}kHz]",
        ),
    )
    return fig


def create_contour_figure(
    sweep_df: pd.DataFrame, controller: GroundStationController
) -> (go.Figure, Position):
    fig = go.Figure()
    bandwidth = sweep_df["psd_bandwidth"].unique()
    if bandwidth.size > 1:
        raise Exception(
            f"Expected only one resolution bandwidth within the same sweep file, but got {bandwidth}"
        )
    bandwidth = bandwidth[0]
    x = sweep_df["measurement_azimuth"]
    y = sweep_df["measurement_elevation"]
    fig.add_trace(
        go.Contour(
            x=x,
            y=y,
            z=sweep_df[f"psd_min"],
            colorbar=dict(
                title=f"PSD [dBFS/{int(bandwidth/1000)}kHz]",  # title here
                titleside="right",
            ),
        )
    )

    x_max, y_max = gaussian_fit_2d_max_pos(
        x=sweep_df["measurement_azimuth"],
        y=sweep_df["measurement_elevation"],
        z=sweep_df[f"psd_min"],
    )

    # max_sigs = sweep_df[sweep_df["psd_min"] > sweep_df["psd_min"].quantile(0.95)]
    # max_sig = max_sigs[["measurement_azimuth", "measurement_elevation"]].mean()
    # x_max = max_sig["measurement_azimuth"]
    # y_max = max_sig["measurement_elevation"]
    max_pos = Position(x_max, y_max)
    angle_az, angle_el = controller.ground_station.antenna.opening_angle

    fig.add_shape(
        type="line",
        x0=x_max,
        y0=y.min(),
        x1=x_max,
        y1=y.max(),
        line=dict(
            color="black",
            width=4,
            dash="dot",
        ),
    )
    fig.add_shape(
        type="line",
        x0=x.min(),
        y0=y_max,
        x1=x.max(),
        y1=y_max,
        line=dict(
            color="black",
            width=4,
            dash="dot",
        ),
    )
    fig.add_shape(
        type="circle",
        xref="x",
        yref="y",
        x0=x_max - angle_az / 2,
        y0=y_max - angle_el / 2,
        x1=x_max + angle_az / 2,
        y1=y_max + angle_el / 2,
        line_color="LimeGreen",
        name="HPBW",
    )
    t_min = pd.to_datetime(sweep_df.timestamp.min(), utc=True).timestamp()
    t_max = pd.to_datetime(sweep_df.timestamp.max(), utc=True).timestamp()
    controller.astro_object.get_position(time_point=t_min)
    sun_df = controller.astro_object.object_path
    sun_df = sun_df[(sun_df["timestamp"] > t_min) & (sun_df["timestamp"] < t_max)]
    sun_df = sun_df[(sun_df.az > x.min()) & (sun_df.az < x.max())]
    sun_df = sun_df[(sun_df.el > y.min()) & (sun_df.el < y.max())]
    if not sun_df.empty:
        fig.add_trace(
            go.Scatter(
                y=sun_df["el"],
                x=sun_df["az"],
                mode="lines",
                line_shape="spline",
                line_color="red",
                name="Sun Path",
            )
        )
    fig.update_layout(
        {"xaxis": {"title": "Azimuth [°]"}, "yaxis": {"title": "Elevation [°]"}}
    )
    return fig, max_pos
