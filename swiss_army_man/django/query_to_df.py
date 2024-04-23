import pandas as pd


def query_to_df(query):
    df = pd.DataFrame(query.values())
    df.columns = df.columns.str.upper()
    return df
