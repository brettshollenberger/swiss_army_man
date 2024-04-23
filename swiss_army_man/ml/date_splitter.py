import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pyarrow as pa
import pyarrow.parquet as pq
from swiss_army_man.utils import project_root, DateUtils
from swiss_army_man.ml import AssetPreprocessor

class DateSplitter():
    X_train = None
    X_test = None
    X_valid = None
    y_train = None
    y_test = None
    y_valid = None
    last_updated = None

    @staticmethod
    def write_split_files(root_path, X_train, X_test, X_valid, y_train, y_test, y_valid, target_col="REV"):
        # Convert to PyArrow Tables
        train_table = pa.Table.from_pandas(X_train)
        test_table = pa.Table.from_pandas(X_test)
        valid_table = pa.Table.from_pandas(X_valid)
        train_target_table = pa.Table.from_pandas(y_train.to_frame(name=target_col))
        test_target_table = pa.Table.from_pandas(y_test.to_frame(name=target_col))
        valid_target_table = pa.Table.from_pandas(y_valid.to_frame(name=target_col))

        pq.write_table(train_table, os.path.join(root_path, 'X_train.parquet'))
        pq.write_table(test_table, os.path.join(root_path, 'X_test.parquet'))
        pq.write_table(valid_table, os.path.join(root_path, 'X_valid.parquet'))
        pq.write_table(train_target_table, os.path.join(root_path, 'y_train.parquet'))
        pq.write_table(test_target_table, os.path.join(root_path, 'y_test.parquet'))
        pq.write_table(valid_target_table, os.path.join(root_path, 'y_valid.parquet'))

        for file in 'X_train', 'X_test', 'X_valid', 'y_train', 'y_test', 'y_valid':
            path = os.path.join(root_path, f"{file}.parquet")
            AssetPreprocessor.dvc_add(path)

        DateSplitter.write_last_updated(root_path)

    @classmethod
    def load_split_files(cls, root_path, target_col="REV"):
        if cls.X_train is None or DateSplitter.files_have_changed(root_path):
            cls.X_train = pd.read_parquet(os.path.join(root_path, 'X_train.parquet'))
            cls.X_test = pd.read_parquet(os.path.join(root_path, 'X_test.parquet'))
            cls.X_valid = pd.read_parquet(os.path.join(root_path, 'X_valid.parquet'))

            cls.y_train = np.array(pd.read_parquet(os.path.join(root_path, 'y_train.parquet'))[target_col])
            cls.y_test = np.array(pd.read_parquet(os.path.join(root_path, 'y_test.parquet'))[target_col])
            cls.y_valid = np.array(pd.read_parquet(os.path.join(root_path, 'y_valid.parquet'))[target_col])

        return cls.X_train, cls.X_test, cls.X_valid, cls.y_train, cls.y_test, cls.y_valid

    @staticmethod
    def set_last_updated(root_path):
        DateSplitter.last_updated = DateSplitter.read_last_updated(root_path)

    @staticmethod
    def last_updated_path(root_path):
        return project_root(f"swiss_army_man/ml/{root_path}dataset_updated.txt")

    @staticmethod
    def read_last_updated(root_path):
        with open(DateSplitter.last_updated_path(root_path), "r") as f:
            return f.read()

    @staticmethod
    def write_last_updated(root_path):
        with open(DateSplitter.last_updated_path(root_path), "w") as f:
            f.write(str(datetime.now()))

    @staticmethod
    def files_have_changed(root_path):
        if DateSplitter.last_updated is None:
            DateSplitter.set_last_updated(root_path)

        return DateSplitter.last_updated != DateSplitter.read_last_updated(root_path)

    @staticmethod
    def validate_splits(X_train, X_test, X_valid, y_train, y_test, y_valid, orig_df, orig_ys):
        assert set(X_train.index).isdisjoint(set(X_test.index)
                                             ), "Overlap between train and validation sets"
        assert set(X_test.index).isdisjoint(set(X_valid.index)
                                            ), "Overlap between train and validation sets"

        # Validate the split
        assert (len(X_train) + len(X_test) + len(X_valid) == len(orig_df))
        assert (len(y_train) + len(y_test) + len(y_valid) == len(orig_ys))
        assert (len(X_train) == len(y_train))
        assert (len(X_test) == len(y_test))
        assert (len(X_valid) == len(y_valid))

        # Validate no records overlap
        assert (set(X_train.index).intersection(set(X_test.index)) == set())
        assert (set(X_train.index).intersection(set(X_valid.index)) == set())
        assert (set(X_test.index).intersection(set(X_valid.index)) == set())

        print("Splits validated.")

    @staticmethod
    def get_split_indexes(file_path, split_col='CREATED_DATE'):
        test_date_start, validation_date_start = DateSplitter.get_date_splits()
        # Read only the necessary columns for filtering
        split_df = pd.read_parquet(file_path, columns=[split_col])
        split_df = DateUtils.standardize_and_sort_dates(split_df)
        split_df = split_df.reset_index(drop=True)
        
        assert split_df[split_col].isna().sum() == 0, "There are NaN dates in the DataFrame"
        
        X_valid = split_df[split_df[split_col] > validation_date_start]
        split_df = split_df[split_df[split_col] <= validation_date_start]
        X_test = split_df[split_df[split_col] > test_date_start]

        # Assuming continuous indices, adjust if not
        train_indices = (0, X_test.index.min())
        test_indices = (X_test.index.min(), X_valid.index.min())
        valid_indices = (X_valid.index.min(), X_valid.index.max() + 1)

        return train_indices, test_indices, valid_indices

    @staticmethod
    def get_date_splits():
        months_test = int(os.getenv('MONTHS_TEST', 2))
        months_validation = int(os.getenv('MONTHS_VALIDATION', 2))
        validation_date_start = DateSplitter.get_days_ago(months_validation * 30)
        test_date_start = DateSplitter.get_days_ago((months_validation + months_test) * 30)

        validation_date_start = f"{validation_date_start} 23:59:59.999999"
        test_date_start = f"{test_date_start} 23:59:59.999999"

        print(f"TEST SET: {test_date_start}")
        print(f"VALIDATION SET: {validation_date_start}")
        assert (pd.to_datetime(test_date_start) <
                pd.to_datetime(validation_date_start))
        return test_date_start, validation_date_start

    @staticmethod
    def split_dataset(file_path, date_col="CREATED_DATE"):
        train_indices, test_indices, valid_indices = DateSplitter.get_split_indexes(file_path, date_col)

        df = pq.read_table(file_path).to_pandas()
        df = DateUtils.standardize_and_sort_dates(df)
        print(f"Train indices: {train_indices[0]} - {train_indices[1]}")
        X_train = df.iloc[train_indices[0]:train_indices[1]]
        X_test = df.iloc[test_indices[0]:test_indices[1]]
        X_valid = df.iloc[valid_indices[0]:valid_indices[1]]

        return X_train, X_test, X_valid

