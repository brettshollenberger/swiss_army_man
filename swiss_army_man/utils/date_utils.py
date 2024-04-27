import re
import random
import numpy as np
import pandas as pd
from scipy.stats import poisson
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

class DateUtils():
    # Input "2024-01-01"
    # Output: "2024-01-01 {random hours/minutes/seconds}"
    @staticmethod
    def get_random_timestamp(date: str, skew: str = 'evening'):
        if skew == 'evening':
            # Generate more sessions in the evening hours (18:00 to 23:59)
            hour = str(np.random.choice(np.concatenate((np.arange(0, 18, 1), np.random.choice(np.arange(18, 24, 1), 3, replace=True))), 1)[0]).zfill(2)
        else:
            hour = str(random.randint(0, 23)).zfill(2)
        minute = str(random.randint(0, 59)).zfill(2)
        seconds = str(random.randint(0, 59)).zfill(2)
        return f"{date} {hour}:{minute}:{seconds}"

    @staticmethod
    def get_days_ago(days_ago: int, date=datetime.now()) -> str:
        x_days_ago = date - timedelta(days=days_ago)
        return x_days_ago.strftime("%Y-%m-%d")

    @staticmethod
    def standardize_date(date: str):
        date = pd.to_datetime(date, errors='coerce')
        if date.tz is not None:
            date = date.tz_convert("UTC")
        else:
            date = pd.to_datetime(date).tz_localize("UTC")
        return date

    @staticmethod
    def standardize_dates(df: pd.DataFrame, date_col: str="CREATED_DATE") -> pd.DataFrame:
        df[date_col] = df[date_col].progress_apply(DateUtils.standardize_date)

        df["DATE"] = pd.to_datetime(df[date_col].dt.date)
        return df

    @staticmethod
    def standardize_and_sort_dates(df: pd.DataFrame, date_col: str):
        df = DateUtils.standardize_dates(df)
        df = df.sort_values(by=[date_col], ascending=True)
        return df

    # Input: "2 days ago"
    # OR "2023-01-01"
    # OR "5 years ago"
    # etc.
    #
    # Output:
    # "2023-01-01"
    # 
    @staticmethod
    def parse_date_str(start_date: str) -> str:
        # List of date formats to check
        date_formats = ["%Y-%m-%d", "%m-%d-%Y"]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(start_date, date_format)
            except ValueError:
                continue

        return DateUtils.parse_relative_date(start_date)

    # This method takes a string representing a date in various formats (e.g., "2 days ago", "2023-01-01", "5 years ago")
    # and returns a standardized date string in the format "YYYY-MM-DD".
    # It first attempts to parse the date using common date formats. If the parsing fails, it then tries to interpret
    # the string as a relative date (e.g., "2 days ago") and calculates the absolute date accordingly.
    @staticmethod
    def parse_relative_date(date_str: str, format="%Y-%m-%d") -> str:
        # Use regular expression to extract number and unit (e.g., days, years)
        match = re.match(r"(\d+)\s+(day|week|month|year|hour|minute|seconds)s?\s+(ago|from now)", date_str)
        if not match:
            raise ValueError("Date string format should be '<number> <days/weeks/months/years> ago'")

        number = int(match.group(1))
        unit = match.group(2)
        ago_from_now = match.group(3)
        if ago_from_now == "ago":
            operation = lambda x: current_date - x
        else:
            operation = lambda x: current_date + x

        # Determine the current date
        current_date = datetime.now()

        # Add/Subtract the appropriate amount of time based on the unit
        if unit == "second":
            offset = timedelta(seconds=number)
        elif unit == "minute":
            offset = timedelta(minutes=number)
        elif unit == "hour":
            offset = timedelta(hours=number)
        elif unit == "day":
            offset = timedelta(days=number)
        elif unit == "week":
            offset = timedelta(weeks=number)
        elif unit == "month":
            offset = relativedelta(months=number)
        elif unit == "year":
            offset = relativedelta(years=number)
        else:
            raise ValueError("Unsupported time unit. Use 'day', 'week', 'month', or 'year'.")

        result = operation(offset)

        if format == "seconds":
            return int((result - current_date).total_seconds())
        else:
            return result.strftime("%Y-%m-%d")

    
    # This method, `date_range`, takes a dictionary of keyword arguments and returns a list of dates between a specified start and end date.
    # It first parses the start and end dates using the `parse_date` method. Then, it generates a pandas date range between these dates.
    # If a specific date format is requested in the keyword arguments, it formats the dates accordingly before returning them as a list.
    @staticmethod
    def date_range(kwargs: dict) -> list:
        start_date, end_date = DateUtils.parse_date(kwargs)
        dates = pd.Series(pd.date_range(start=start_date, end=end_date))
        if "format" in kwargs.keys():
            dates = dates.dt.strftime(kwargs["format"])
        return dates.tolist()

    @staticmethod
    def parse_date(kwargs: dict) -> list:
        format = "%Y-%m-%d"
        end_date = datetime.now().strftime(format)
        if kwargs.get("start_date"):
            start_date = DateUtils.parse_date_str(kwargs.get("start_date"))
        elif kwargs.get("interval_end_datetime"):
            start_date = kwargs.get("interval_start_datetime").strftime(format)
            end_date = kwargs.get("interval_end_datetime").strftime(format)
        else:
            start_date = DateUtils.get_days_ago(1)

        return start_date, end_date

    @staticmethod
    def group_by_time_period(dates_list: list, period: str) -> list:
        df = pd.DataFrame({'Date': pd.to_datetime(dates_list)})
        df.set_index('Date', inplace=True)
        grouped = []
        for _, group in df.resample(period):
            dates = group.index.strftime('%Y-%m-%d').tolist()
            if period == 'H':
                dates = [date.strftime('%Y-%m-%d %H:00') for date in group.index]
            grouped.append(dates)
        return grouped

    # Given a datetime, add minutes based on a poisson distribution (e.g. most of the time, the median number of minutes
    # will be added, but sometimes it will extend into the rest of the distribution)
    @staticmethod
    def add_minutes_poisson(date: str, avg_minutes_to_add: int) -> str:
        minutes = poisson.rvs(avg_minutes_to_add)
        date = date + timedelta(minutes=minutes)
        seconds = str(random.randint(0, 59)).zfill(2)
        return ":".join(f"{date}".split(":")[0:2] + [seconds])
