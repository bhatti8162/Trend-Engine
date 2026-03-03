import pandas as pd
import numpy as np

def scalp_demand_supply_pro(
    client,
    symbol="BTCUSDT",
    interval="5m",
    higher_tf="1h",
    ema_period=25,
):
    """
    Advanced 5m Demand/Supply detector.
    - Detects real imbalance (impulse move)
    - Uses volume confirmation
    - ATR adaptive logic
    - 1H trend alignment
    - Returns: (demand: bool, supply: bool)
    """

    # =========================
    # Fetch 5m Data
    # =========================
    klines = client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=100
    )

    df = pd.DataFrame(klines, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df[["open","high","low","close","volume"]] = df[
        ["open","high","low","close","volume"]
    ].astype(float)

    current_price = df["close"].iloc[-1]

    # =========================
    # EMA
    # =========================
    df["ema"] = df["close"].ewm(span=ema_period, adjust=False).mean()
    ema_now = df["ema"].iloc[-1]

    # =========================
    # ATR
    # =========================
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift()),
            abs(df["low"] - df["close"].shift())
        )
    )
    df["atr"] = df["tr"].rolling(14).mean()
    atr = df["atr"].iloc[-1]

    # =========================
    # Detect Impulse Candle
    # =========================
    df["body"] = abs(df["close"] - df["open"])
    df["avg_volume"] = df["volume"].rolling(20).mean()

    impulse = df[
        (df["body"] > atr * 1.2) &  # strong body
        (df["volume"] > df["avg_volume"])  # volume spike
    ]

    demand = False
    supply = False

    if not impulse.empty:
        last_impulse = impulse.iloc[-1]

        # Bullish impulse → Demand zone
        if last_impulse["close"] > last_impulse["open"]:
            zone_low = last_impulse["low"]
            zone_high = last_impulse["open"]  # base area

            if zone_low <= current_price <= zone_high:
                if current_price > ema_now:
                    demand = True

        # Bearish impulse → Supply zone
        if last_impulse["close"] < last_impulse["open"]:
            zone_high = last_impulse["high"]
            zone_low = last_impulse["open"]

            if zone_low <= current_price <= zone_high:
                if current_price < ema_now:
                    supply = True

    # =========================
    # Higher TF Confirmation
    # =========================
    htf_klines = client.get_klines(
        symbol=symbol,
        interval=higher_tf,
        limit=ema_period + 5
    )

    df_htf = pd.DataFrame(htf_klines, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df_htf["close"] = df_htf["close"].astype(float)
    df_htf["ema"] = df_htf["close"].ewm(span=ema_period, adjust=False).mean()

    htf_price = df_htf["close"].iloc[-1]
    htf_ema = df_htf["ema"].iloc[-1]

    if demand and htf_price < htf_ema:
        demand = False

    if supply and htf_price > htf_ema:
        supply = False

    return bool(demand), bool(supply)