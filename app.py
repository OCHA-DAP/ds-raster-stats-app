import json
import os
from datetime import date, datetime

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import ctx, dcc, html
from dash.dependencies import Input, Output, State
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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
    # fixed="top",
    color="primary",
    dark=True,
)

load_dotenv()

AZURE_DB_PW = os.getenv("AZURE_DB_PW")
MODE = os.getenv("MODE")
ENGINE_URL = f"postgresql+psycopg2://chdadmin:{AZURE_DB_PW}@chd-rasterstats-dev.postgres.database.azure.com/postgres"
# TODO: Optimize this further
engine = create_engine(ENGINE_URL)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Raster Stats Viz"


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
                "Your selected dataset has monthly averaged values. All dates selected within the same month will return the same data.",
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


# App layout
app.layout = html.Div(
    [
        # TODO: Not gonna be performant
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
                                        dmc.LoadingOverlay(
                                            html.Div(
                                                id="grid",
                                                style={
                                                    "marginTop": "15px",
                                                },
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


def display_date_range(dataset, date):
    if dataset == "imerg":
        return [pd.to_datetime(date), pd.to_datetime(date)]
    else:
        date = datetime.strptime(date, "%Y-%m-%d")
        next_month = date.replace(day=1) + relativedelta(months=1)
        last_day = next_month - relativedelta(days=1)
        return [pd.to_datetime(date), pd.to_datetime(last_day)]


def to_first_of_month(date_string):
    date = datetime.strptime(date_string, "%Y-%m-%d")
    first_of_month = date.replace(day=1)
    return first_of_month.strftime("%Y-%m-%d")


def load_geojson(iso3, adm_level):
    file_path = f"data/{iso3}_adm{adm_level.lower()}.geojson"
    with open(file_path, "r") as f:
        return json.load(f)


def calculate_centroid(geojson):
    gdf = gpd.GeoDataFrame.from_features(geojson["features"])
    centroid = gdf.geometry.unary_union.centroid
    return centroid.y, centroid.x


# Function to fetch data from the database
def fetch_data_from_db(iso3, adm_level, dataset, lt=None):

    con = engine.connect()
    if not lt:
        query = text(
            f"SELECT * FROM public.{dataset} WHERE iso3='{iso3}' AND adm_level='{adm_level}'"
        )
    else:
        query = text(
            f"SELECT * FROM public.{dataset} WHERE iso3='{iso3}' AND adm_level={adm_level} AND leadtime='{lt}'"
        )
    df = pd.read_sql_query(query, con)
    df.valid_date = pd.to_datetime(df.valid_date)
    df = df.sort_values("valid_date", ascending=True)
    con.close()
    engine.dispose()

    return df


@app.callback(
    Output("line", "figure"),
    Input("pcodes", "value"),
    Input("date-picker", "value"),
    Input("stat-dropdown", "value"),
    State("df-store", "data"),
    State("ds-dropdown", "value"),
)
def create_line_chart(pcodes, date, stat, df_store, dataset):
    df = pd.DataFrame.from_dict(df_store)
    df_ = df[df.pcode.isin(pcodes)]
    line_chart = px.line(
        df_, x="valid_date", y=stat, template="simple_white", color="pcode"
    )
    line_chart.update_layout(margin={"r": 0, "t": 15, "l": 0, "b": 0}, xaxis_title="")
    date_range = display_date_range(dataset, date)
    line_chart.add_vrect(
        x0=date_range[0],
        x1=date_range[1],
        opacity=0.2,
        line_width=5,
        line_color="red",
        fillcolor="red",
    )
    return line_chart


@app.callback(
    Output("pcodes", "data"), Output("pcodes", "value"), Input("df-store", "data")
)
def update_pcodes(df_store):
    df = pd.DataFrame.from_dict(df_store)
    pcodes = df.pcode.unique()
    return pcodes, [pcodes[0]]


@app.callback(
    Output("lt-dropdown", "disabled"),
    Output("date-info", "style"),
    Input("ds-dropdown", "value"),
)
def dataset_display(dataset):
    if dataset == "seas5":
        return False, {"width": 200}
    elif dataset == "era5":
        return True, {"width": 200}
    elif dataset == "imerg":
        return True, {"display": "None"}


# Callback to load GeoJSON when ISO3 is selected
@app.callback(
    Output("geojson-store", "data"),
    Input("iso3-dropdown", "value"),
    Input("admin-level-dropdown", "value"),
)
def load_geojson_data(iso3_code, adm_level):
    if iso3_code:
        geojson = load_geojson(iso3_code, adm_level)
        return geojson
    return None


@app.callback(
    Output("info", "children"),
    Output("info", "title"),
    Input("df-store", "data"),
    State("ds-dropdown", "value"),
)
def data_info(df, dataset):
    return "To do: Info for selected dataset", f"{len(df)} rows returned for {dataset}"


# Callback to update the map
@app.callback(
    Output("map", "figure"),
    Output("grid", "children"),
    Output("df-store", "data"),
    Input("iso3-dropdown", "value"),
    Input("admin-level-dropdown", "value"),
    Input("date-picker", "value"),
    Input("ds-dropdown", "value"),
    Input("lt-dropdown", "value"),
    Input("stat-dropdown", "value"),
    Input("geojson-store", "data"),
    Input("df-store", "data"),
)
def update_charts(iso3, admin_level, date, dataset, lt, stat, geojson, df_store):
    print("updating charts...")
    # Calculate centroid
    center_lat, center_lon = calculate_centroid(geojson)

    # Get new data from database
    if (
        ctx.triggered_id
        in [
            "iso3-dropdown",
            "admin-level-dropdown",
            "ds-dropdown",
            "lt-dropdown",
            "geojson-store",
        ]
        and MODE != "local"
    ):
        print("getting new data...")
        lt = None if dataset in ["era5", "imerg"] else lt
        df = fetch_data_from_db(iso3, admin_level, dataset, lt)
        df_return = df.to_dict("records")
        ag_grid = data_grid(df)
    elif MODE == "local":
        print("getting cached local data...")
        df = pd.read_csv("data/demo-export.csv")
        df.columns = [x.lower() for x in df.columns]
        df_return = df.to_dict("records")
        ag_grid = data_grid(df)
    else:
        print("retrieving data from store...")
        df = pd.DataFrame.from_dict(df_store)
        df.valid_date = pd.to_datetime(df.valid_date)
        df_return = dash.no_update
        ag_grid = dash.no_update

    # These are the datasets with only monthly data
    if dataset in ["seas5", "era5"]:
        date = to_first_of_month(date)

    df_ = df[df.valid_date == pd.to_datetime(date)]

    map_chart = px.choropleth_map(
        df_,
        geojson=geojson,
        locations="pcode",
        color=stat,
        color_continuous_scale="Blues",
        map_style="carto-positron",
        zoom=4,
        center={"lat": center_lat, "lon": center_lon},
        featureidkey=f"properties.ADM{admin_level}_PCODE",
        opacity=0.5,
    )
    map_chart.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return map_chart, ag_grid, df_return


if __name__ == "__main__":
    app.run_server(debug=True)
