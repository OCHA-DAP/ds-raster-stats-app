import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, ctx
from sqlalchemy import text
from utils.data_processing import get_engine

from constants import MODE
from utils.components import data_grid
from utils.data_processing import calculate_centroid, fetch_data_from_db, load_geojson
from utils.date_utils import display_date_range, to_first_of_month


def register_callbacks(app):
    @app.callback(
        Output("ag-grid-table", "exportDataAsCsv"),
        Input("csv-download", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_data_as_csv(n_clicks):
        if n_clicks:
            return True
        return False

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
        line_chart.update_layout(
            margin={"r": 0, "t": 15, "l": 0, "b": 0}, xaxis_title=""
        )
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
        return (
            "To do: Info for selected dataset",
            f"{len(df)} rows returned for {dataset}",
        )

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

    @app.callback(
        Output("completeness-table", "rowData"),
        Output("completeness-table", "selectedRows"),
        Input("ds-dropdown", "value"),
    )
    def update_completeness_table(dataset):
        engine = get_engine(MODE)
        query = text("SELECT * FROM public.iso3")
        query_completeness = text(f"SELECT * FROM public.{dataset}_completeness")

        with engine.connect() as con:
            df_all_iso3s = pd.read_sql_query(query, con)
            df_completeness = pd.read_sql_query(query_completeness, con)
            df_merged = df_all_iso3s[
                ["iso3", "stats_last_updated", "total-pcodes", "max_adm_level"]
            ].merge(df_completeness, on="iso3", how="left")
            df_grouped = (
                df_merged.groupby("iso3")
                .agg(
                    {
                        "stats_last_updated": "first",
                        "max_adm_level": "first",
                        "total-pcodes": "first",
                        "year": "count",
                        "total_rows": "sum",
                        "unique_pcodes": "first",
                    }
                )
                .reset_index()
            )

        # TODO -- Calculate expected vals dynamically based on current date
        ds_factor = {"era5": 525, "seas5": 526 * 7, "imerg": 8690}
        ds_date_updated = {
            "era5": "2024-10-10",
            "seas5": "2024-10-09",
            "imerg": "2024-10-11",
        }

        df_grouped["total_rows_correct"] = (
            ds_factor[dataset] * df_grouped["total-pcodes"]
        )
        # TODO -- Pull from DB instead of hard-coding
        df_grouped["stats_last_updated"] = ds_date_updated[dataset]
        df_dict = df_grouped.to_dict("records")
        return df_dict, [df_dict[0]]

    @app.callback(
        Output("completeness-table-detail", "rowData"),
        Input("completeness-table", "selectedRows"),
        State("ds-dropdown", "value"),
    )
    def populate_detail_table(selected, dataset):
        engine = get_engine(MODE)
        query = text(
            f"SELECT * FROM public.{dataset}_completeness WHERE iso3='{selected[0]['iso3']}'"  # noqa
        )  
        with engine.connect() as con:
            df = pd.read_sql_query(query, con)
        return df.to_dict("records")
