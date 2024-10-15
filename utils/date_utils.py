from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta


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
