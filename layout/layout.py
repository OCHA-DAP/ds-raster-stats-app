import dash_mantine_components as dmc
from dash import dcc, html

from utils.components import (
    chart_panel,
    mantine_sidebar_panel,
    navbar,
    database_completeness,
    database_details,
)


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
                                            # dmc.Button(
                                            #     style={"marginTop": "15px"},
                                            #     children="Download as CSV",
                                            #     variant="outline",
                                            #     fullWidth=True,
                                            #     id="csv-download",
                                            # ),
                                            dmc.LoadingOverlay(
                                                html.Div(
                                                    id="grid",
                                                )
                                            ),
                                        ],
                                        value="table",
                                    ),
                                    dmc.TabsPanel(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        children=database_completeness(),
                                                        style={
                                                            "backgroundColor": "red",
                                                            "width": "50%",
                                                        },
                                                        id="completeness-table-div",
                                                    ),
                                                    html.Div(
                                                        children=database_details(),
                                                        style={
                                                            "backgroundColor": "green",
                                                            "width": "50%",
                                                        },
                                                        id="green",
                                                    ),
                                                ],
                                                style={
                                                    "display": "flex",
                                                    "height": "500px",
                                                },
                                            ),
                                        ],
                                        value="db",
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
