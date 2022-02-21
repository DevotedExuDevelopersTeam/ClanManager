from datetime import datetime, timedelta
from re import search


def to_discord_timestamp(delta: timedelta):
    return f"<t:{int((datetime.now() + delta).timestamp())}>"


def extract_regex(value: str, name: str) -> str:
    name = name.upper() + "::"
    pattern = name + r".*"

    match = search(pattern, value)
    if match is None:
        return None
    else:
        return match.group().replace(name, "")
