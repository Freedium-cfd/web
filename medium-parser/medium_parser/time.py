from datetime import datetime


def convert_datetime_to_human_readable(unix_time: int):
    """Converts a datetime object to a human-readable format.

    Args:
      unix_time: The datetime object to convert.

    Returns:
      A human-readable string representing the datetime object.
    """
    datetime_object = datetime.fromtimestamp(unix_time / 1000)

    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    day = datetime_object.day
    month = month_names[datetime_object.month - 1]
    year = datetime_object.year

    human_readable_string = f"{month} {day}, {year}"

    return human_readable_string


def get_unix_ms() -> int:
    # Get the current date and time
    current_date_time = datetime.now()

    # Convert to the number of milliseconds since January 1, 1970 (Unix Epoch time)
    milliseconds_since_epoch = int(current_date_time.timestamp() * 1000)

    return milliseconds_since_epoch
