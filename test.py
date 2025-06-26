import requests

def get_klines(symbol='BANUSDT', interval='5m', limit=3):
    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

def average_dollar_volume(symbol='BANUSDT', limit=3):
    klines = get_klines(symbol, limit=limit)
    dollar_volumes = []

    for candle in klines:
        close_price = float(candle[4])  # цена закрытия
        volume = float(candle[5])       # объём монет
        dollar_volume = close_price * volume
        dollar_volumes.append(dollar_volume)

    avg_dollar_volume = sum(dollar_volumes) / len(dollar_volumes)
    print(f"Средний проходной объём в долларах за последние {limit} свечей (5м) для {symbol}: {avg_dollar_volume:.6f}")

    last_dollar_volume = dollar_volumes[-1]
    print(f"Проходной объём в долларах последней 5-минутной свечи: {last_dollar_volume:.6f}")

# Пример вызова с 3 свечами
average_dollar_volume(limit=3)
