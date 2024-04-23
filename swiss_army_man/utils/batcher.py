import pandas as pd
from datetime import datetime
from . import DateUtils

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
        date_range = DateUtils.date_range(kwargs)
        if batch_size == "week":
            return DateUtils.group_by_time_period(date_range, 'W')
        elif batch_size == "day":
            return DateUtils.group_by_time_period(date_range, 'D')
        elif batch_size == "hour":
            return DateUtils.group_by_time_period(date_range, 'H')
        elif batch_size == "month":
            return DateUtils.group_by_time_period(date_range, 'M')
        elif batch_size == "year":
            return DateUtils.group_by_time_period(date_range, 'A')
        return date_range

    @staticmethod
    def start_and_end(batches):
        return [[batch[0], batch[-1]] for batch in batches]
