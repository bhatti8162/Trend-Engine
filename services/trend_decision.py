def get_decision_on_signal(
        trend_map,
        ema_trend_map,
        vwap_trend_map,
        atr_map,
        adx_map,
        rsi_map):

    """
    Fully weighted multi-timeframe decision engine.
    Uses every indicator + timeframe independently.
    Returns: one-line description + confidence 0-10
    """

    # ========================
    # EXTRACT
    # ========================
    t1h = trend_map.get("1h")
    t15 = trend_map.get("15m")
    t5  = trend_map.get("5m")

    ema1h = ema_trend_map.get("1h")
    ema15 = ema_trend_map.get("15m")
    ema5  = ema_trend_map.get("5m")

    vwap1h  = vwap_trend_map.get("1h")
    vwap15  = vwap_trend_map.get("15m")
    vwap5   = vwap_trend_map.get("5m")

    atr1h = atr_map.get("1h")
    atr15 = atr_map.get("15m")

    adx1h = adx_map.get("1h")
    adx15 = adx_map.get("15m")

    rsi5  = rsi_map.get("5m")
    rsi15 = rsi_map.get("15m")

    required = [t1h,t15,t5,ema1h,ema15,ema5,
                vwap1h,vwap15,vwap5,
                atr1h,atr15,adx1h,adx15,
                rsi5,rsi15]

    if not all(required):
        return "Insufficient data"

    # ========================
    # WEIGHTS (Higher TF stronger)
    # ========================
    weights = {
        "1h": 3,
        "15m": 2,
        "5m": 1
    }

    direction_score = 0
    environment_score = 0
    timing_score = 0

    # ========================
    # TREND MAP
    # ========================
    for tf, value in [("1h", t1h), ("15m", t15), ("5m", t5)]:
        if value == "BULLISH":
            direction_score += weights[tf]
        elif value == "BEARISH":
            direction_score -= weights[tf]

    # ========================
    # EMA STRUCTURE
    # ========================
    for tf, value in [("1h", ema1h), ("15m", ema15), ("5m", ema5)]:
        if value == "BULLISH":
            direction_score += weights[tf] * 0.8
        elif value == "BEARISH":
            direction_score -= weights[tf] * 0.8

    # ========================
    # VWAP INSTITUTIONAL BIAS
    # ========================
    for tf, value in [("1h", vwap1h), ("15m", vwap15), ("5m", vwap5)]:
        if value == "ABOVE":
            direction_score += weights[tf] * 0.7
        elif value == "BELOW":
            direction_score -= weights[tf] * 0.7

    # ========================
    # ADX (TREND STRENGTH)
    # ========================
    for tf, adx in [("1h", adx1h), ("15m", adx15)]:
        _, val = adx
        if val >= 30:
            environment_score += weights[tf] * 0.7
        elif val >= 25:
            environment_score += weights[tf] * 0.4
        else:
            environment_score -= weights[tf] * 0.5

    # ========================
    # ATR (VOLATILITY)
    # ========================
    for tf, atr in [("1h", atr1h), ("15m", atr15)]:
        state, _ = atr
        if state == "HIGH":
            environment_score += weights[tf] * 0.3
        elif state == "LOW":
            environment_score -= weights[tf] * 0.3

    # ========================
    # RSI (TIMING ONLY)
    # ========================
    for tf, rsi in [("15m", rsi15), ("5m", rsi5)]:
        _, val = rsi
        if 45 <= val <= 60:
            timing_score += weights[tf] * 0.4
        elif val < 30 or val > 70:
            timing_score -= weights[tf] * 0.4

    # ========================
    # FINAL CALCULATION
    # ========================
    raw_score = abs(direction_score) + environment_score + timing_score

    confidence = max(0, min(10, round(raw_score)))

    # Bias
    if direction_score > 4:
        bias = "Bullish"
    elif direction_score < -4:
        bias = "Bearish"
    else:
        bias = "Sideways"

    # Description
    if bias == "Bullish" and confidence >= 7:
        desc = "Strong Bullish Continuation"
    elif bias == "Bullish":
        desc = "Weak Bullish – internal conflict"
    elif bias == "Bearish" and confidence >= 7:
        desc = "Strong Bearish Continuation"
    elif bias == "Bearish":
        desc = "Weak Bearish – internal conflict"
    else:
        desc = "Sideways – mixed structure"

    return f"{desc} | Confidence: {confidence}/10"