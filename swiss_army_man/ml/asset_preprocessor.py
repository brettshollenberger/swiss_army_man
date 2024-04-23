import re
import os
import subprocess
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.impute import SimpleImputer
from swiss_army_man.utils import project_root, grep
from pyhelpers.store import save_pickle, load_pickle
from fastai.tabular.all import add_datepart as fastai_add_datepart

# Asset Preprocess handles imputation of medians,  filling of NAs, and handling of categorical data
# on the training data, as well as application of the same transformations on the inference data.
#
# It's used by calling AssetPreprocessor.preprocess(df, args) to preprocess the training data, and
# then AssetPreprocessor.postprocess(df) to apply the same transformations to the test, validation, and inference data.
#
class AssetPreprocessor():
    VERBOSE = False
    CATEGORICAL_COMMON_MIN = 50

    @staticmethod
    def stage_required_files(required_files):
        no_dvc_files = [file for file in required_files if not re.search(".dvc", file)]

        for file in no_dvc_files:
            AssetPreprocessor.dvc_add(file)
            dvc_file = f"{file}.dvc"
            AssetPreprocessor.git_add(file)
            AssetPreprocessor.git_add(dvc_file)


    @staticmethod
    def save_pickle(asset, path):
        return AssetPreprocessor.save_asset("pkl", asset, path)

    @staticmethod
    def save_joblib(asset, path):
        return AssetPreprocessor.save_asset("joblib", asset, path)

    @staticmethod
    def save_parquet(asset, path):
        return AssetPreprocessor.save_asset("parquet", asset, path)

    @staticmethod
    def dvc_add(path):
        if not re.match("bart_pipeline/bart_pipeline", path):
            path = project_root(path)
        env = os.environ.copy()
        print(subprocess.run(f'poetry run dvc add {path}', shell=True, capture_output=True, text=True, env=env))
        AssetPreprocessor.git_add(path)

    @staticmethod
    def git_push():
        command = f'git push'
        env = os.environ.copy()
        print(subprocess.run(command, shell=True, capture_output=True, text=True, env=env).stdout)

    @staticmethod
    def git_branch(branch_name):
        command = f'git checkout -b {branch_name}'
        print(command)
        env = os.environ.copy()
        print(subprocess.run(command, shell=True, capture_output=True, text=True, env=env).stdout)

    @staticmethod
    def git_commit(message, skip_checks=False):
        skip_checks_part = "\n\nskip-checks: true" if skip_checks else ""
        command = f'git commit -m "{message}" {skip_checks_part}'
        print(command)
        env = os.environ.copy()
        print(subprocess.runcommand(command, shell=True, capture_output=True, text=True, env=env).stdout)

    @staticmethod
    def git_add(path):
        command = f'git add {path}'
        print(command)
        env = os.environ.copy()
        print(subprocess.run(command, shell=True, capture_output=True, text=True, env=env).stdout)

    @staticmethod
    def dvc_push():
        print("poetry run dvc push")
        env = os.environ.copy()
        print(subprocess.run(f'poetry run dvc push', shell=True, capture_output=True, text=True, env=env).stdout)

    @staticmethod
    def prepare_commit():
        AssetPreprocessor.dvc_resolve()
        AssetPreprocessor.dvc_push()

    @staticmethod
    def dvc_resolve():
        command = f'poetry run dvc resolve | sort'
        print(command)
        env = os.environ.copy()
        output = subprocess.run(command, shell=True, capture_output=True, text=True, env=env).stdout

    @staticmethod
    def save_asset(type, asset, path):
        root_path = os.path.dirname(path)
        os.makedirs(root_path, exist_ok=True)
        if type == "pkl":
            save_pickle(asset, path)
        elif type == "joblib":
            joblib.dump(asset, path)
        elif type == "parquet":
            asset.to_parquet(path)
        else:
            raise ValueError(f"Unknown asset type {type}")

        AssetPreprocessor.dvc_add(path)
        return True

    @staticmethod
    def set_verbose(verbose):
        AssetPreprocessor.VERBOSE = verbose

    def __init__(self, dir):
        self.DIRECTORY = dir

    def required_files(self):
        files = os.listdir(self.DIRECTORY)
        required_file_types = ["pkl", "joblib", "parquet", "json"]
        required_files = [ os.path.join(self.DIRECTORY, file) for file in files if re.search("|".join(required_file_types), file) ]
        non_dvc_files = [ os.path.join(self.DIRECTORY, file) for file in required_files if not re.search(".dvc", file) ]
        dvc_files = [ f"{file}.dvc" for file in non_dvc_files ]
        missing_dvc_files = [ file for file in dvc_files if not os.path.exists(file) ]
        for file in missing_dvc_files:
            AssetPreprocessor.dvc_add(file)

        return [
            *non_dvc_files,
            *dvc_files
        ]

    def output_file_path(self):
        return os.path.join(self.DIRECTORY, "preprocessing_output.json")

    def file_path(self):
        return os.path.join(self.DIRECTORY, "preprocessing_args.pkl")

    def postprocess(self, df):
        args = self.load_preprocessing_args()
        if self.VERBOSE:
            print(f"Loaded preprocessing args: {args}")
        df, _ = self.handle_args(df, args)
        print("Postprocessing complete.")
        return df

    def preprocess(self, df, args={}, verbose=False):
        self.set_verbose(verbose)
        print("Preprocessing...")
        df, output = self.handle_args(df, args, preprocessing=True)

        self.save_preprocessing_args(args)
        self.save_preprocessing_output(output)
        self.set_verbose(False)
        return output

    def handle_args(self, df, args, preprocessing=False):
        output = pd.DataFrame({})
        order = ["clip", "categorical", "impute_median", "ffill", "fillna", "fill_date", "add_datepart", "custom"]
        args = {k: args[k] for k in order if k in args}

        for key, value in args.items():
            callable = getattr(self, f"{'preprocess_' if preprocessing else ''}{key}")
            if isinstance(value, list):
                for col in value:
                    df, output_val = callable(df, col)
                    output[col] = [output_val]
            else:
                for col, value in value.items():
                    if key == "custom":
                        callable = value
                    df, output_val = callable(df, col, value)
                    output[col] = [output_val]
        return df, output

    def save_preprocessing_output(self, output):
        output.to_csv(self.output_file_path(), index=False)

    def load_preprocessing_output(self):
        return pd.read_csv(self.output_file_path())

    def save_preprocessing_args(self, args):
        return AssetPreprocessor.save_pickle(args, self.file_path())

    def load_preprocessing_args(self):
        return load_pickle(self.file_path())

    def prepare_for_imputation(self, df, col):
        df = df.assign(**{col: pd.to_numeric(df[col], errors="coerce")})
        df[col] = np.where(df[col].isnull(), np.nan, df[col]) # Convert "<NA>" to NaN for imputer
        if col not in df.columns:
            shaped = np.full(len(df), np.nan).reshape(-1, 1)
        else:
            shaped = np.array(df[col]).reshape(-1, 1)
        return shaped

    def preprocess_impute_median(self, df, col):
        if self.VERBOSE:
            print(f"Imputing median for {col} using SimpleImputer...")

        shaped = self.prepare_for_imputation(df, col)
        imputer = SimpleImputer(strategy="median")
        imputer.fit(shaped)
        joblib_file = os.path.join(self.DIRECTORY, f"imputer.{col}.joblib")
        AssetPreprocessor.save_joblib(imputer, joblib_file)
        df = df.assign(**{col: imputer.transform(shaped)})
        return df, df[col].median()

    def impute_median(self, df, col): 
        joblib_file = os.path.join(self.DIRECTORY, f"imputer.{col}.joblib")
        imputer = joblib.load(joblib_file)

        if self.VERBOSE:
            print(f"Imputing median for {col} using median value {imputer.statistics_[0]}...")

        shaped = self.prepare_for_imputation(df, col)
        df = df.assign(**{col: imputer.transform(shaped)})
        return df, imputer.statistics_[0]

    def preprocess_fillna(self, df, col, default):
        df, _ = self.fillna(df, col, default)
        return df, default

    def fillna(self, df, col, default):
        if self.VERBOSE:
            print(f"Filling NAs for {col} with {default}")

        if col not in df.columns:
            df = df.assign(**{col: np.full(len(df), default)})
        else:
            df = df.assign(**{col: df[col].fillna(default)})
        return df, default

    def preprocess_fill_date(self, df, col, args):
        how = args.get("training", "fill")
        if how == "ffill":
            return self.preprocess_ffill(df, col)

    def fill_date(self, df, col, args):
        how = args.get("inference", "today")
        if how == "today":
            if self.VERBOSE:
                print(f"Filling date for {col} with today's date...")

            if col in df.columns:
                df = df.assign(**{col: pd.to_datetime(df[col], errors="coerce")})
                df = df.assign(**{col: df[col].fillna(datetime.now())})
            else:
                df = df.assign(**{col: datetime.now()})
        return df, df[col].max()

    def categorical(self, df, col):
        common_values =  load_pickle(os.path.join(self.DIRECTORY, f"cat_feature_{col}.pkl"))
        if self.VERBOSE:
            print(f"Handling categorical data for {col} with allowed values {common_values}...")
        return df.assign(**{f"{col}": np.where(df[col].isin(common_values), df[col], "OTHER")}), common_values

    def preprocess_categorical(self, df, col):
        counts = df[col].value_counts()
        common_values = list(counts[counts > AssetPreprocessor.CATEGORICAL_COMMON_MIN].index)
        AssetPreprocessor.save_pickle(common_values, os.path.join(self.DIRECTORY, f"cat_feature_{col}.pkl"))
        df, common_values = self.categorical(df, col)
        return df, common_values

    def preprocess_add_datepart(self, df, col):
        df, col = self.add_datepart(df, col)
        return df, None
    
    def add_datepart(self, df, col):
        prefix = f"{col}_"
        original_col = df[col].copy()
        df = df.copy()
        df = fastai_add_datepart(df, col,
                          prefix=prefix, drop=False)
        date_cols = grep(df, prefix)
        rename = {col: col.replace(prefix, "").upper()
                  for col in date_cols}
        df = df.rename(columns=rename)
        df = df.rename(columns={"DAYOFWEEK": "DAY_OF_WEEK", "DAYOFYEAR": "DAY_OF_YEAR"})
        df = df.assign(**{col: original_col})
        return df, None

    def preprocess_clip(self, df, col, args):
        return self.clip(df, col, args)

    def clip(self, df, col, args):
        min_val = args.get("min", None)
        max_val = args.get("max", None)
        df = df.assign(**{col: df[col].clip(min_val, max_val)})
        return df, args

    def preprocess_ffill(self, df, col):
        return self.ffill(df, col)

    def ffill(self, df, col):
        if self.VERBOSE:
            print(f"Filling NAs for {col} with forward fill...")

        df = df.assign(**{col: df[col].ffill()})
        return df, None