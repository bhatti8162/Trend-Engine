import pandas as pd

def scalp_support_resistance_smart(client, symbol="BTCUSDT", interval="5m", candles=6, ema_period=25):
    """
    Returns supporting/resisting signals optimized for scalping:
    - Checks trend using 25 EMA
    - Uses adaptive buffer based on micro range
    - Only returns supporting/resisting
    """

    klines = client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=max(candles, ema_period)
    )

    df = pd.DataFrame(klines, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df[["high","low","close"]] = df[["high","low","close"]].astype(float)

    # Micro structure
    df_micro = df.tail(candles)
    micro_high = df_micro["high"].max()
    micro_low = df_micro["low"].min()
    micro_range = micro_high - micro_low

    current_price = df["close"].iloc[-1]

    # EMA trend
    df["ema_25"] = df["close"].ewm(span=ema_period, adjust=False).mean()
    ema_25 = df["ema_25"].iloc[-1]
    trend_bullish = current_price > ema_25

    # Adaptive buffer
    buffer = max(micro_range * 0.1, current_price * 0.005)

    supporting = trend_bullish and current_price <= micro_low + buffer
    resisting = (not trend_bullish) and current_price >= micro_high - buffer

    # Convert to native bool (important for JSON)
    return bool(supporting), bool(resisting)