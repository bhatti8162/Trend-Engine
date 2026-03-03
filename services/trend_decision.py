def get_decision_on_signal(
    trend_map,
    ema_trend_map,
    vwap_trend_map,
    atr_map,
    adx_map,
    rsi_map
):
    """
    Regime-based decision engine.
    Detects real market states before assigning bias.
    Returns: description + confidence 0-10
    """

    tf_weights = {"1h": 2.0, "15m": 1.0, "5m": 0.5}

    # =========================
    # 1️⃣ STRUCTURE SCORE
    # =========================
    direction_score = 0
    alignment_count = 0

    for tf in tf_weights:
        w = tf_weights[tf]

        t = trend_map.get(tf)
        e = ema_trend_map.get(tf)
        v = vwap_trend_map.get(tf)

        bullish = sum([
            t == "BULLISH",
            e in ("UP", "ABOVE"),
            v == "ABOVE"
        ])

        bearish = sum([
            t == "BEARISH",
            e in ("DOWN", "BELOW"),
            v == "BELOW"
        ])

        if bullish > bearish:
            direction_score += w
            alignment_count += 1
        elif bearish > bullish:
            direction_score -= w
            alignment_count += 1

    # Determine base bias
    if direction_score >= 2:
        bias = "Bullish"
    elif direction_score <= -2:
        bias = "Bearish"
    else:
        bias = "Neutral"

    # =========================
    # 2️⃣ TREND STRENGTH (ADX)
    # =========================
    strong_trend = 0
    weak_trend = 0

    for tf, (_, val) in adx_map.items():
        if val >= 30:
            strong_trend += tf_weights.get(tf, 0)
        elif val < 20:
            weak_trend += tf_weights.get(tf, 0)

    # =========================
    # 3️⃣ VOLATILITY (ATR)
    # =========================
    high_vol = 0
    low_vol = 0

    for tf, (state, _) in atr_map.items():
        if state == "HIGH":
            high_vol += tf_weights.get(tf, 0)
        elif state == "LOW":
            low_vol += tf_weights.get(tf, 0)

    # =========================
    # 4️⃣ MOMENTUM EXTREME (RSI)
    # =========================
    overbought = 0
    oversold = 0

    for tf, (_, val) in rsi_map.items():
        if val > 70:
            overbought += tf_weights.get(tf, 0)
        elif val < 30:
            oversold += tf_weights.get(tf, 0)

    # =========================
    # 5️⃣ MARKET REGIME LOGIC
    # =========================

    # --- Strong continuation ---
    if strong_trend >= 2 and high_vol >= 1.5 and bias != "Neutral":
        desc = f"Strong {bias} Trend – Continuation Environment"
        confidence = 8.5

    # --- Weak trend ---
    elif strong_trend >= 1 and low_vol >= 1 and bias != "Neutral":
        desc = f"Weak {bias} – Low Volatility Drift"
        confidence = 5.5

    # --- Ranging market ---
    elif weak_trend >= 2 and low_vol >= 1.5:
        desc = "Ranging Market – Mean Reversion Environment"
        confidence = 4.0

    # --- Compression before breakout ---
    elif strong_trend >= 1 and low_vol >= 2:
        desc = "Volatility Compression – Breakout Likely"
        confidence = 6.0

    # --- Exhaustion ---
    elif overbought >= 2 and bias == "Bullish":
        desc = "Bullish Trend Exhaustion – Pullback Risk"
        confidence = 5.0

    elif oversold >= 2 and bias == "Bearish":
        desc = "Bearish Trend Exhaustion – Bounce Risk"
        confidence = 5.0

    # --- Conflict / Chop ---
    elif alignment_count <= 1:
        desc = "Choppy Structure – No Clear Direction"
        confidence = 3.0

    # --- Neutral ---
    else:
        desc = "Mixed Conditions – Low Edge"
        confidence = 4.5

    return f"{desc} | Confidence: {confidence:.2f}"