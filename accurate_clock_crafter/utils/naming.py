def format_time(hour: int, minute: int) -> str:
    return f"{hour:02d}{minute:02d}"


def get_minute_from_png(name: str) -> int:
    if not name.endswith(".png"):
        return -1
    try:
        minute = int(name[:-4])
    except ValueError:
        return -1
    return minute if 0 <= minute < 60 else -1


def pack_resource_key(pack_name: str) -> str:
    return pack_name.lower()
