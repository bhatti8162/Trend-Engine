import requests
from config import CMC_KEY

def get_change(symbol="BTC"):

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_KEY
    }

    params = {
        "symbol": symbol.upper(),
        "convert": "USD"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status", {}).get("error_code") != 0:
            print("CMC Error:", data.get("status", {}).get("error_message"))
            return None, None

        quote = data["data"][symbol.upper()]["quote"]["USD"]

        percent_1h = quote.get("percent_change_1h")
        percent_24h = quote.get("percent_change_24h")

        return (
            round(percent_1h, 2) if percent_1h is not None else None,
            round(percent_24h, 2) if percent_24h is not None else None
        )

    except Exception as e:
        print("Error:", e)
        return None, None