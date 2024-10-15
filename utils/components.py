from datetime import date

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            html.A(
                html.Img(src="assets/centre_banner_greenbg.png", height=40),
                href="https://centre.humdata.org/data-science/",
            ),
        ),
    ],
    style={"height": "60px", "margin": "0px", "padding": "10px"},
    brand="Raster Stats Visualizer",
    color="primary",
    dark=True,
)


def data_grid(df):
    return dag.AgGrid(
        id="ag-grid-table",
        rowData=df.to_dict("records"),
        defaultColDef={"filter": True},
        csvExportParams={
            "fileName": "demo-export.csv",
        },
        columnDefs=[{"field": i} for i in df.columns],
        style={"height": 600},
        dashGridOptions={"pagination": True, "paginationAutoPageSize": True},
        className="ag-theme-material",
    )


def mantine_sidebar_panel():
    return html.Div(
        style={"padding": "20px"},
        children=[
            dmc.Select(
                label="Select dataset",
                id="ds-dropdown",
                value="era5",
                data=["era5", "seas5", "imerg"],
                style={"width": 200, "marginBottom": 10},
            ),
            dmc.Select(
                label="Select a stat",
                id="stat-dropdown",
                value="mean",
                data=[
                    "mean",
                    "median",
                    "max",
                    "min",
                    "count",
                    "sum",
                    "std",
                ],
                style={"width": 200, "marginBottom": 10},
            ),
            dmc.Select(
                label="Select a leadtime month",
                id="lt-dropdown",
                value="0",
                data=["0", "1", "2", "3", "4", "5", "6"],
                style={"width": 200, "marginBottom": 10},
            ),
            dmc.Select(
                label="Select an ISO3 code",
                id="iso3-dropdown",
                value="AFG",
                data=["AFG", "ETH", "MDV", "BRA"],
                style={"width": 200, "marginBottom": 10},
            ),
            dmc.Select(
                label="Select an admin level",
                id="admin-level-dropdown",
                value="1",
                data=["0", "1", "2"],
                style={"width": 200, "marginBottom": 10},
            ),
            dmc.DatePicker(
                id="date-picker",
                label="Valid date",
                minDate=date(1981, 1, 1),
                value=date(2020, 1, 1),
                style={"width": 200, "marginBottom": 10},
            ),
            dmc.Alert(
                """Your selected dataset has monthly averaged values. 
                All dates selected within the same month will return the same data.
                """,
                title="Monthly average",
                style={"width": 200, "marginBottom": 10},
                id="date-info",
            ),
            dmc.MultiSelect(
                id="pcodes",
                label="Select PCODE(s) to display on line chart",
                style={"width": 200, "marginTop": 20},
                maxSelectedValues=5,
            ),
        ],
    )


def chart_panel():
    return html.Div(
        [
            dmc.LoadingOverlay(
                dcc.Graph(
                    id="line",
                    style={"height": "150px"},
                )
            ),
            dmc.LoadingOverlay(
                dcc.Graph(
                    id="map",
                    style={
                        "height": "calc(100% - 250px)",
                    },
                )
            ),
        ],
        style={"float": "left", "boxSizing": "border-box", "width": "100%"},
    )
