import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html

from utils.components import chart_panel, mantine_sidebar_panel, navbar


def create_layout():
    return html.Div(
        [
            dcc.Store(id="geojson-store"),
            dcc.Store(id="df-store"),
            navbar,
            html.Div(
                [
                    mantine_sidebar_panel(),
                    html.Div(
                        style={"width": "calc(100% - 250px)", "marginTop": "30px"},
                        children=[
                            dmc.Alert(
                                "Fetching results from database...",
                                style={"marginBottom": "20px"},
                                id="info",
                            ),
                            dmc.Tabs(
                                [
                                    dmc.TabsList(
                                        [
                                            dmc.Tab("Charts", value="charts"),
                                            dmc.Tab("Selected Data", value="table"),
                                            dmc.Tab("Database Summary", value="db"),
                                        ]
                                    ),
                                    dmc.TabsPanel([chart_panel()], value="charts"),
                                    dmc.TabsPanel(
                                        [
                                            dmc.Button(
                                                style={"marginTop": "15px"},
                                                children="Download as CSV",
                                                variant="outline",
                                                fullWidth=True,
                                                id="csv-download",
                                            ),
                                            dmc.LoadingOverlay(
                                                html.Div(
                                                    id="grid",
                                                )
                                            ),
                                        ],
                                        value="table",
                                    ),
                                    dmc.TabsPanel(
                                        [dmc.Alert("TODO!", color="red")], value="db"
                                    ),
                                ],
                                orientation="horizontal",
                                value="charts",
                            ),
                        ],
                    ),
                ],
                style={"display": "flex", "flexWrap": "wrap"},
            ),
        ]
    )
