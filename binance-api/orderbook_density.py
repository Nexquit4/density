import requests
import time

def get_mark_price(symbol):
    """Получаем рыночную цену с Binance Futures"""
    url = 'https://fapi.binance.com/fapi/v1/premiumIndex'
    params = {'symbol': symbol}
    response = requests.get(url, params=params)
    data = response.json()
    return float(data['markPrice'])


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


def average_dollar_volume(symbol='BANUSDT', limit=5):
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
    return avg_dollar_volume


def get_futures_order_book(symbol='BANUSDT', limit=100, price_range=0.01):
    url = 'https://fapi.binance.com/fapi/v1/depth'
    params = {'symbol': symbol.upper(), 'limit': limit}
    response = requests.get(url, params=params)
    data = response.json()
    if 'asks' not in data or 'bids' not in data:
        print("Ошибка в ответе:")
        print(data)
        return 
    price = get_mark_price('BANUSDT')
    avg = average_dollar_volume(limit=5)

    for price_str, qty_str in data['asks']:
        qty_asks = float(qty_str)*price
        if qty_asks >= avg:
            print(f"Цена: ${price_str} | Сумма: ${float(qty_str)*price}")
        
    for price_str, qty_str in data['bids']:
        qty_bids = float(qty_str)*price
        if qty_bids >= avg:
            print(f"Цена: ${price_str} | Сумма: ${float(qty_str)*price}")





# Пример вызова с 3 свечами
#average_dollar_volume(limit=3)        
#price = get_mark_price('BANUSDT')
get_futures_order_book()
