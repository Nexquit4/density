import requests
import time

def get_mark_price(symbol):
    """Получаем рыночную цену с Binance Futures"""
    url = 'https://fapi.binance.com/fapi/v1/premiumIndex'
    params = {'symbol': symbol}
    response = requests.get(url, params=params)
    data = response.json()
    return float(data['markPrice'])

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

    for price_str, qty_str in data['asks']:
        print(f"Цена: ${price_str} | Сумма: ${float(qty_str)*price}")

    for price_str, qty_str in data['bids']:
        print(f"Цена: ${price_str} | Сумма: ${float(qty_str)*price}")
        
#price = get_mark_price('BANUSDT')
get_futures_order_book()