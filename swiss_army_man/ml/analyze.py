from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from dateutil.parser import parse
from datetime import datetime, date, time, timedelta
import pandas as pd
import re


def count_nulls_by_month(df, column, timestamp_column="CREATED_DATE"):
    df = df.copy()
    df[timestamp_column] = pd.to_datetime(
        df[timestamp_column], errors="coerce")
    df["MONTH"] = df[timestamp_column].apply(lambda x: x.month)
    df["YEAR"] = df[timestamp_column].apply(lambda x: x.year)

    agg = df.groupby(["YEAR", "MONTH"]).agg(
        total_count=(column, 'size'),
        null_count=(column, lambda x: x.isnull().sum())
    ).reset_index()

    # Calculate percent nulls
    agg['PERCENT_NULL'] = (agg['null_count'] / agg['total_count']) * 100

    agg["DATE"] = pd.to_datetime(
        agg['YEAR'].astype(str) + '-' + agg['MONTH'].astype(str).progress_apply(lambda x: x.rjust(2, '0')) + '-01', errors="coerce")

    plt.figure(figsize=(15, 5))
    plt.scatter(agg["DATE"], agg["PERCENT_NULL"])
    plt.show()
    return agg


def missing_columns(df):
    nulls = df.isna()
    zeros = df == 0
    missing_data = nulls | zeros
    columns_with_missing_data = missing_data.all()
    return columns_with_missing_data[columns_with_missing_data == True].keys()

def columns_with_empty_string(df):
    for column in df.columns:
        if "" in df[column].value_counts().keys():
            print(column)

def columns_with_pct_null(df, pct=0.05):
    for column in df.columns:
        if df[column].isnull().mean() > pct:
            print(column)

def rows_with_any_nulls(df):
    rows_w_nulls = pd.DataFrame()
    columns = columns_with_nulls(df)
    for column in columns:
        rows_w_nulls = pd.concat([rows_w_nulls, df[df[column].isnull()]])
    return rows_w_nulls.drop_duplicates()

def remove_rows_with_nulls(df):
    rows_with_nulls = rows_with_any_nulls(df)
    print(f"Dropping {len(rows_with_nulls)} rows with null values")
    df = df.drop(rows_with_nulls.index)
    return df

def columns_with_nulls(df):
    columns = []
    for column in df.columns:
        if True in df[column].isna().value_counts().keys():
            columns.append(column)
    return columns


def count_nulls(data, column):
    print(data[column].isnull().value_counts())


def is_date(d):
    return isinstance(d, (datetime, date, time, timedelta, pd.Timestamp, pd.Period, pd.Timedelta, np.datetime64))


def grep(data, search):
    pattern = re.compile(search)
    return [col for col in data if pattern.search(col)]


def grep_col(df, search):
    col_idx = df.columns
    pattern = re.compile(search)
    return [col for col in col_idx if pattern.search(col)]


def is_lambda_function(func):
    return callable(func) and func.__name__ == "<lambda>"


def plot_percent_converted(data, column):
    totals = data[column].value_counts().to_dict()
    conv = data.groupby([column, "DID_CONVERT"]
                        ).size().reset_index(name="COUNT")
    conv = conv[conv["DID_CONVERT"] == True]
    conv["PERCENT_CONVERTED"] = conv["COUNT"] / [totals[value]
                                                 for value in conv[column]]
    plt.figure(figsize=(15, 5))
    plt.scatter(conv[column], conv["PERCENT_CONVERTED"])
    plt.show()


def bucketize(data, column, q=4, labels=lambda x, y: x):
    band_name = f'{column}_BAND'
    is_date_ = False

    if is_date(data[column][0]):
        time_name = f'{column}_TIME'
        data[time_name] = [time.to_numpy().astype(int)
                           for time in data[column]]
        is_date_ = True
        column = time_name

    if is_lambda_function(labels):
        ntiles = pd.qcut(data[column], q=q).value_counts().keys()
        boundaries = [[x.left, x.right] for x in ntiles]

        if is_date_:
            boundaries = [pd.to_datetime(boundary).strftime(
                "%Y-%m-%d") for boundary in boundaries]

        boundaries = sorted(boundaries)
        labels = [labels(boundary[0], boundary[1]) for boundary in boundaries]

    data[band_name] = pd.qcut(data[column], q=q, labels=labels)
    return data


def bucketize_and_correlate(data, column, q=4, labels=lambda x, y: x):
    plottable = bucketize(data.copy(), column, q, labels)
    band_name = f'{column}_BAND'
    plot_percent_converted(plottable, band_name)
    return


def clip_col(data, col):
    data = data.copy()
    data[col] = np.clip()
    return data


def impute_median(data, col):
    data = data.copy()
    col_data = pd.DataFrame(data[col])
    imputer = SimpleImputer(strategy="median")
    imputer.fit(col_data)
    imputed_data = pd.DataFrame(imputer.transform(col_data), columns=[col])
    data = data.drop(columns=[col])
    merged = pd.merge(data, imputed_data, left_index=True, right_index=True)
    return merged


def bool_to_int(data):
    data = data.copy()
    int_types = data.select_dtypes(include=[bool]).astype(int)
    keep_columns = np.array(set(data.columns) - set(int_types.columns))
    data = data.loc[:, keep_columns].merge(
        int_types, left_index=True, right_index=True)
    return data


def forward_fill(data, column):
    data.sort_values('CREATED_DATE', inplace=True)
    data[column].fillna(method='ffill', inplace=True)

    return data


def feature_importance(model, df):
    return pd.DataFrame({'cols': df.columns, 'imp': model.feature_importances_}
                        ).sort_values('imp', ascending=False)
