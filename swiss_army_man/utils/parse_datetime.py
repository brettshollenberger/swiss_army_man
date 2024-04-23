import re
from datetime import datetime

def parse_datetime(timestamp):
    # List of formats to try
    if not isinstance(timestamp, str):
        timestamp = str(timestamp)

    parse_formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%d %H:%M:%S.%f%z',
    ]

    for parse_str in parse_formats:
        try:
            dt = datetime.strptime(timestamp, parse_str)
            return dt
        except ValueError:
            continue  # Try the next format