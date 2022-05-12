"""
Utils for working with filepaths.
"""
import os
from pathlib import Path
import datetime
import logging
import pytz

def find_all_matching_files(name, path):
    """
    Finds all files matching filename within path.

    :param name (str): file name to search
    :param path (str): path to search within
    :returns (list): returns list of matching paths to filenames or empty list if no matches found. 
    """
    result = []
    for root, _, files in os.walk(path):
        if name in files:
            result.append(Path(os.path.join(root, name)))
    return result


def validate_filepath(filepath):
    filepath = Path(filepath)
    assert filepath.exists()
    return filepath


def timezone_converter(timestamp, source_tz, destination_tz, fmt=None):
    """
    Converts timestamp from a source timezone to a destination timezone. 
    To see commonly used timezone options run: 
    
    ```from pytz import common_timezones```
    
    :param timestamp: (datetime.datetime) timestamp to convert
    :param source_tz: (pytz.timezone) source timezone to convert 
    :param destination_tz: (pytz.timezone) destination timezone
    :param fmt: (str) optional - timestamp format to pass to strftime
    
    :returns: (datetime.datetime) converted timestamp
    """
    dest_obj = pytz.timezone(destination_tz)
    source_obj = pytz.timezone(source_tz).localize(timestamp.replace(tzinfo=None))
    converted = dest_obj.normalize(source_obj.astimezone(dest_obj))
    return converted if fmt is None else converted.strftime(fmt)


def get_file_modification_time(filepath, timezone, fmt=None):
    """
    Gets modification time of file.
    
    :param filepath: (patlib.Path or str) path to file
    :timezone: (str) desired timezone in pytz format (e.g. 'US/Central')
    :fmt: optional (str) timestamp format to pass to strftime 
    
    :returns: datetime object
    """
    ts = datetime.datetime.fromtimestamp(Path(filepath).stat().st_mtime, tz=datetime.timezone.utc)
    return timezone_converter(ts, 'UTC', timezone, fmt=fmt)


def append_timestamp_to_filepath(filepath, timestamp, separator='__', with_suffix=None, verbose=True, return_filepath=False):
    """
    Appends timestamp to provided filepath (but before the file extension)
    
    :param filepath: (patlib.Path or str) filepath to directory or file to modify
    :param timestamp: (str or datetime object) timestamp to append
    :param with_suffix: (str) desired alternate file extension to replace existing extension. 
        By default, original extension will be maintained.
    :param verbose: (bool) logs renamed filepath
    :param return_filepath: (bool) returns renamed filepath patlib.Path
    """
    filepath = Path(filepath)  
    filepath_rn = filepath.with_name(f'{filepath.stem}{separator}{timestamp}').with_suffix(filepath.suffix if with_suffix is None else with_suffix)
    filepath.rename(filepath_rn)
    if verbose:
        logging.info(f'File renamed: {filepath_rn}')
    if return_filepath:
        return filepath_rn