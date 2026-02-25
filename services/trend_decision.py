def get_decision_on_signal(
    trend_map,
    ema_trend_map,
    vwap_trend_map,
    atr_map,
    adx_map,
    rsi_map
):
    """
    Fully weighted multi-timeframe decision engine.
    Uses multiple indicators independently.
    Returns: one-line description + confidence 0-10
    """

    # ========================
    # WEIGHTS (displayed at top)
    # ========================
    # Timeframe weights (higher TF dominates)
    tf_weights = {"1h": 1.5, "15m": 1, "5m": 0.5}
    # Indicator multipliers
    indicator_mult = {"trend": 1.0, "ema": 0.8, "vwap": 0.7, "adx": 0.6, "atr": 0.4, "rsi": 0.5}

    # ========================
    # EXTRACT
    # ========================
    tf_list = ["1h", "15m", "5m"]
    required = []

    def extract_values(map_, tfs):
        vals = {}
        for tf in tfs:
            val = map_.get(tf)
            vals[tf] = val
            required.append(val)
        return vals

    trend = extract_values(trend_map, tf_list)
    ema = extract_values(ema_trend_map, tf_list)
    vwap = extract_values(vwap_trend_map, tf_list)
    atr = extract_values({k: atr_map.get(k) for k in ["1h", "15m"]}, ["1h", "15m"])
    adx = extract_values({k: adx_map.get(k) for k in ["1h", "15m"]}, ["1h", "15m"])
    rsi = extract_values({k: rsi_map.get(k) for k in ["15m", "5m"]}, ["15m", "5m"])

    if not all(required):
        return "Insufficient data"

    direction_score = 0
    environment_score = 0
    timing_score = 0

    # ========================
    # HELPER: Score directional indicators (trend/EMA/VWAP)
    # ========================
    def score_direction(values, mult=1.0):
        score = 0
        for tf, val in values.items():
            w = tf_weights[tf] * mult
            if val in ("BULLISH", "ABOVE"):
                score += w
            elif val in ("BEARISH", "BELOW"):
                score -= w
        return score

    direction_score += score_direction(trend, indicator_mult["trend"])
    direction_score += score_direction(ema, indicator_mult["ema"])
    direction_score += score_direction(vwap, indicator_mult["vwap"])

    # ========================
    # ADX (trend strength scaling)
    # ========================
    for tf, (state, val) in adx.items():
        w = tf_weights[tf] * indicator_mult["adx"]
        if val >= 30:
            environment_score += w
        elif val >= 25:
            environment_score += w * 0.6
        else:
            environment_score -= w * 0.5

    # ========================
    # ATR (volatility scaling)
    # ========================
    for tf, (state, _) in atr.items():
        w = tf_weights[tf] * indicator_mult["atr"]
        if state == "HIGH":
            environment_score += w
        elif state == "LOW":
            environment_score -= w

    # ========================
    # RSI (timing scaling)
    # ========================
    for tf, (_, val) in rsi.items():
        w = tf_weights[tf] * indicator_mult["rsi"]
        if 45 <= val <= 60:
            timing_score += w
        elif val < 30 or val > 70:
            timing_score -= w

    # ========================
    # FINAL CALCULATION
    # ========================
    net_direction = direction_score
    raw_score = max(0, net_direction + environment_score + timing_score)
    confidence = min(10, round(raw_score))

    # ========================
    # BIAS
    # ========================
    if net_direction > 2:
        bias = "Bullish"
    elif net_direction < -2:
        bias = "Bearish"
    else:
        bias = "Sideways"

    # ========================
    # DESCRIPTION
    # ========================
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