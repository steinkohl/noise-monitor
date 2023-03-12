from dash import Dash, dcc, html
from base64 import b64encode
import io
import pandas as pd


from .plotly_figures import create_3d_figure, create_contour_figure
from ..ground_station import GroundStationController


def display_results(controller: GroundStationController, sweep_df: pd.DataFrame = None):
    """This function launches a dash web server to display the results of the noise sweep data.

    :param controller: The initialized controller class of the ground station which recorded the data
    :param sweep_df: The measurement data, collected during noise sweep. If None, the previous measured data is used.
    :return: None
    """
    if sweep_df is None:
        sweep_df = controller.get_measurement_points_as_dataframe()
    title = "Noise Monitor"
    app = Dash(title)
    buffer_3d = io.StringIO()
    buffer_con = io.StringIO()

    fig_3d = create_3d_figure(sweep_df)
    fig_con, max_position = create_contour_figure(sweep_df, controller)

    fig_3d.write_html(buffer_3d)
    fig_con.write_html(buffer_con)

    html_bytes_3d = buffer_3d.getvalue().encode()
    encoded_3d = b64encode(html_bytes_3d).decode()

    html_bytes_con = buffer_con.getvalue().encode()
    encoded_con = b64encode(html_bytes_con).decode()

    oaz, oel = controller.ground_station.antenna.opening_angle
    pos_tol = controller.ground_station.rotator.get_positioning_tolerance()

    app.layout = html.Div(
        [
            html.H2(title),
            html.H4("Noise sweep of PSD values displayed as 3D scatter"),
            dcc.Graph(id="graph_3d", figure=fig_3d),
            html.A(
                html.Button("Download 3D graph as static HTML"),
                id="download_3d",
                href="data:text/html;base64," + encoded_3d,
                download="3d_scatter.html",
            ),
            html.H4("Contour plot of the min PSD values"),
            html.H6(
                "The contour plot shows the distribution of the minimum PSD levels."
            ),
            html.H6(
                "The intersection of the two dotted lines shows the maximum of estimated Gaussian distribution of the "
                f"radiation source at {max_position.azimuth:.2f} azimuth and {max_position.elevation:.2f} elevation."
            ),
            html.H6(f"The inaccuracy of the estimated position is thereby at least {pos_tol:.2f}° due to the rotator"
                    " resolution."),
            html.H6(
                "The green ellipse shows the half power band width of "
                f"{oaz:.2f}° azimuth and {oel:.2f}° elevation."
            ),
            html.H6(
                "If present, the red line shows the estimated path of the sun during the measurement."
            ),
            dcc.Graph(id="graph_con", figure=fig_con),
            html.A(
                html.Button("Download contour graph as static HTML"),
                id="download_con",
                href="data:text/html;base64," + encoded_con,
                download="contour_plot.html",
            ),
        ]
    )

    print("Press CTRL+C to quit")
    app.run_server(
        debug=True,
        port=controller.port,
        host=controller.ip,
    )
