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

def standardize_dates(df, date_col="CREATED_DATE"):
    df[date_col] = df[date_col].progress_apply(standardize_date)

    df["DATE"] = pd.to_datetime(df[date_col].dt.date)
    return df

def standardize_and_sort_dates(df, date_col):
    df = standardize_dates(df)
    df = df.sort_values(by=[date_col], ascending=True)
    return df
