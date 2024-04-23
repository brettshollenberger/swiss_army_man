import re
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class Batcher():
    # Can be used to split either into batches of fixed size or date ranges, for example:
    #
    # You have a list of ids: items=list(range(0,100)), kwargs={"batch_size": 10}
    #   - Splits into batches of 10
    #
    # Or, you have no list, just date range:
    # kwargs={"batch_size": "week", "start_date": "2021-01-01"}
    #   - Generates a list of each week start + end between 2021-01-01 and today
    #
    @staticmethod
    def generate_batches(items = [], kwargs = {}):
        batches = Batcher.get_batches(items, kwargs)
        batches = Batcher.start_and_end(batches)
        uuids = [{'block_uuid': f'batch_{i}'} for i in range(len(batches))]
        return [ batches, uuids ]

    @staticmethod
    def get_days_ago(days_ago, date=datetime.now()):
        x_days_ago = date - timedelta(days=days_ago)
        return x_days_ago.strftime("%Y-%m-%d")

    @staticmethod
    def parse_date(kwargs):
        format = "%Y-%m-%d"
        end_date = datetime.now().strftime(format)
        if kwargs.get("start_date"):
            start_date = Batcher.parse_date_str(kwargs.get("start_date"))
        elif kwargs.get("interval_end_datetime"):
            start_date = kwargs.get("interval_start_datetime").strftime(format)
            end_date = kwargs.get("interval_end_datetime").strftime(format)
        else:
            start_date = Batcher.get_days_ago(1)

        return start_date, end_date

    @staticmethod
    def date_range(kwargs):
        start_date, end_date = Batcher.parse_date(kwargs)
        dates = pd.date_range(start=start_date, end=end_date)
        return [date for date in dates]

    @staticmethod
    def group_by_time_period(dates_list, period):
        df = pd.DataFrame({'Date': pd.to_datetime(dates_list)})
        df.set_index('Date', inplace=True)
        grouped = []
        for _, group in df.resample(period):
            dates = group.index.strftime('%Y-%m-%d').tolist()
            if period == 'H':
                dates = [date.strftime('%Y-%m-%d %H:00') for date in group.index]
            grouped.append(dates)
        return grouped

    @staticmethod
    def get_batches(items = [], kwargs = {}):
        batch_size = kwargs.get("batch_size")
        # If batch size is a number, split it up that way,
        # otherwise it might be week, day, hour, month, year, etc.
        try:
            batch_size = int(batch_size)
            # Split items into groups of batch_size
            return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        except ValueError:
            pass
        date_range = Batcher.date_range(kwargs)
        if batch_size == "week":
            return Batcher.group_by_time_period(date_range, 'W')
        elif batch_size == "day":
            return Batcher.group_by_time_period(date_range, 'D')
        elif batch_size == "hour":
            return Batcher.group_by_time_period(date_range, 'H')
        elif batch_size == "month":
            return Batcher.group_by_time_period(date_range, 'M')
        elif batch_size == "year":
            return Batcher.group_by_time_period(date_range, 'A')
        return date_range

    @staticmethod
    def start_and_end(batches):
        return [[batch[0], batch[-1]] for batch in batches]

    @staticmethod
    def parse_date_str(start_date):
        # List of date formats to check
        date_formats = ["%Y-%m-%d", "%m-%d-%Y"]
        
        # Try parsing the date with each format
        print(start_date)
        for date_format in date_formats:
            try:
                return datetime.strptime(start_date, date_format)
            except ValueError:
                continue

        return Batcher.parse_relative_date(start_date)

    @staticmethod
    def parse_relative_date(date_str):
        # Use regular expression to extract number and unit (e.g., days, years)
        match = re.match(r"(\d+)\s+(day|week|month|year)s?\s+ago", date_str)
        if not match:
            raise ValueError("Date string format should be '<number> <days/weeks/months/years> ago'")

        number = int(match.group(1))
        unit = match.group(2)

        # Determine the current date
        current_date = datetime.now()

        # Subtract the appropriate amount of time based on the unit
        if unit == "day":
            result_date = current_date - timedelta(days=number)
        elif unit == "week":
            result_date = current_date - timedelta(weeks=number)
        elif unit == "month":
            result_date = current_date - relativedelta(months=number)
        elif unit == "year":
            result_date = current_date - relativedelta(years=number)
        else:
            raise ValueError("Unsupported time unit. Use 'day', 'week', 'month', or 'year'.")

        return result_date.strftime("%Y-%m-%d")
