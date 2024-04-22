import os
from datetime import datetime

def files_modified_since(file_paths, since_date):
    if type(since_date) == str:
        since_date = datetime.strptime(since_date, '%Y-%m-%d').timestamp()
    return get_last_modified_dates([file_path for file_path in file_paths if os.path.getmtime(file_path) > since_date])

def max_last_modified(file_paths):
    return datetime.fromtimestamp(max([os.path.getmtime(file_path) for file_path in file_paths])).stftime('%Y-%m-%d %H:%M:%S')

def get_last_modified_dates(file_paths):
    """
    Takes a list of file paths and returns a dictionary with filenames as keys 
    and their last modified dates as values.
    
    Parameters:
    - file_paths: List of strings, where each string is a path to a file.
    
    Returns:
    - A dictionary with filenames as keys and their last modified dates as values.
    """
    last_modified_dict = {}
    for file_path in file_paths:
        try:
            # Get the last modified time of the file
            mod_time = os.path.getmtime(file_path)
            # Convert the modification time to a readable format
            mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            # Add to the dictionary
            last_modified_dict[file_path] = mod_date
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    return last_modified_dict

