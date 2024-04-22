import pandas as pd
from tqdm import tqdm
tqdm.pandas()

def standardize_date(date):
    date = pd.to_datetime(date, errors='coerce')
    if date.tz is not None:
        date = date.tz_convert("UTC")
    else:
        date = pd.to_datetime(date).tz_localize("UTC")
    return date

def standardize_dates(df):
    df["CREATED_DATE"] = df["CREATED_DATE"].progress_apply(standardize_date)

    df["DATE"] = pd.to_datetime(df["CREATED_DATE"].dt.date)
    return df

def standardize_and_sort_dates(df):
    df = standardize_dates(df)
    df = df.sort_values(by=["CREATED_DATE"], ascending=True)
    return df
