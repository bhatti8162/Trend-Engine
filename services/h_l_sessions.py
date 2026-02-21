# from binance.client import Client
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
from collections import OrderedDict


# ==============================
# SESSION TIMES (UTC DAY BASED)
# ==============================
SESSIONS = {
    "Tokyo":    {"start": 1,  "end": 9},    # 00:00–09:00 UTC
    "London":   {"start": 8,  "end": 17},   # 08:00–17:00 UTC
    "New_York": {"start": 13, "end": 22},   # 13:00–22:00 UTC
}


def format_time(dt, tz_name):
    local_time = dt.astimezone(ZoneInfo(tz_name))

    if tz_name.upper() == "UTC":
        return local_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return local_time.strftime("%I:%M:%S %p")


def utc_hour_to_datetime(utc_hour: int, date: datetime.date):
    return datetime.datetime.combine(
        date,
        datetime.time(utc_hour, 0),
        tzinfo=datetime.timezone.utc
    )


def get_all_session_high_low(client, symbol, interval="5m"):
    results = {}

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    today = now.date()

    times = OrderedDict([
        ("UTC", format_time(now, "UTC")),
        ("PK", format_time(now, "Asia/Karachi")),
        ("London", format_time(now, "Europe/London")),
        ("New_York", format_time(now, "America/New_York")),
        ("Tokyo", format_time(now, "Asia/Tokyo")),
    ])

    for session, info in SESSIONS.items():
        start_hour = info["start"]
        end_hour   = info["end"]

        # ALWAYS build today's session window
        session_start = utc_hour_to_datetime(start_hour, today)
        session_end   = utc_hour_to_datetime(end_hour, today)

        # Determine status
        if now < session_start:
            status = "Not Started"
        elif session_start <= now <= session_end:
            status = "Active"
        else:
            status = "Finished"

        try:
            klines = client.get_klines(
                symbol=symbol,
                interval=interval,
                startTime=int(session_start.timestamp() * 1000),
                endTime=int(session_end.timestamp() * 1000),
            )

            if not klines:
                results[session] = {
                    "status": status,
                    "high": None,
                    "low": None,
                }
                continue

            df = pd.DataFrame(klines, columns=[
                "open_time","open","high","low","close","volume",
                "close_time","quote_asset_volume","num_trades",
                "taker_buy_base","taker_buy_quote","ignore"
            ])

            df["high"] = df["high"].astype(float)
            df["low"]  = df["low"].astype(float)

            results[session] = {
                "status": status,
                "high": float(df["high"].max()),
                "low":  float(df["low"].min()),
            }

        except Exception as e:
            results[session] = {
                "status": "Error",
                "message": str(e),
            }

    return {
        "current_times": times,
        "sessions": results
    }