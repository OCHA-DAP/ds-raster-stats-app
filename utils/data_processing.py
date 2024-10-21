import json

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text

from constants import MODE, AZURE_DB_PW_DEV, AZURE_DB_PW_PROD


def get_engine(mode):
    if mode == "prod":
        url = f"postgresql+psycopg2://chdadmin:{AZURE_DB_PW_PROD}@chd-rasterstats-prod.postgres.database.azure.com/postgres"
    else:
        url = f"postgresql+psycopg2://chdadmin:{AZURE_DB_PW_DEV}@chd-rasterstats-dev.postgres.database.azure.com/postgres"
    return create_engine(url)


engine = get_engine(MODE)


def fetch_data_from_db(iso3, adm_level, dataset, lt=None):
    con = engine.connect()
    if not lt:
        query = text(
            f"SELECT * FROM public.{dataset} WHERE iso3='{iso3}' AND adm_level='{adm_level}'"  # noqa
        )
    else:
        query = text(
            f"SELECT * FROM public.{dataset} WHERE iso3='{iso3}' AND adm_level={adm_level} AND leadtime='{lt}'"  # noqa
        )
    df = pd.read_sql_query(query, con)
    df.valid_date = pd.to_datetime(df.valid_date)
    df = df.sort_values("valid_date", ascending=True)
    con.close()
    engine.dispose()
    return df


def load_geojson(iso3, adm_level):
    file_path = f"data/{iso3.lower()}_adm{adm_level}.geojson"
    with open(file_path, "r") as f:
        return json.load(f)


def calculate_centroid(geojson):
    gdf = gpd.GeoDataFrame.from_features(geojson["features"])
    centroid = gdf.geometry.unary_union.centroid
    return centroid.y, centroid.x


def get_table_row_count(engine):
    tables = ["era5", "seas5", "imerg"]
    results = {}
    with engine.connect() as connection:
        for table in tables:
            result = connection.execute(text(f"SELECT COUNT(*) FROM public.{table}"))
            results.update({table: result.scalar()})
        return results
