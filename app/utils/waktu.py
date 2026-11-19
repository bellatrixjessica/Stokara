from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7), "WIB")


def sekarang():
    return datetime.now(timezone.utc)


def sekarang_wib():
    return datetime.now(WIB)
