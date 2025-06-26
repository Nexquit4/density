import requests
import time

def get_order_book(symbol='BANUSDT', limit=100):
    url = 'https://fapi.binance.com/fapi/v1/depth'
    params = {'symbol': symbol, 'limit': limit}
    return requests.get(url, params=params).json()

def get_mark_price(symbol='BANUSDT'):
    url = 'https://fapi.binance.com/fapi/v1/premiumIndex'
    return float(requests.get(url, params={'symbol': symbol}).json()['markPrice'])

def get_klines(symbol='BANUSDT', limit=5):
    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {'symbol': symbol, 'interval': '5m', 'limit': limit}
    return requests.get(url, params=params).json()

def get_avg_dollar_volume(symbol='BANUSDT'):
    klines = get_klines(symbol)
    volumes = [float(c[4]) * float(c[5]) for c in klines]  # close_price * volume
    return sum(volumes) / len(volumes)

def find_strongest_density(snapshot, avg_volume, mark_price, threshold=1.5):
    densities = []

    for side in ['bids', 'asks']:
        for price_str, qty_str in snapshot[side][:50]:
            price = float(price_str)
            qty = float(qty_str)
            total_usd = price * qty

            if total_usd >= avg_volume * threshold:
                densities.append({
                    'side': side,
                    'price': price_str,
                    'qty': qty_str,
                    'usd': total_usd
                })

    return max(densities, key=lambda d: d['usd'], default=None)

def track_density(symbol='BANUSDT', watch_seconds=10):
    avg_volume = get_avg_dollar_volume(symbol)
    mark_price = get_mark_price(symbol)
    print(f"\n📊 Средний проходной объём за 5м: ${avg_volume:.2f}")

    snapshot = get_order_book(symbol)
    density = find_strongest_density(snapshot, avg_volume, mark_price)

    if not density:
        print("❌ Нет плотностей, превышающих средний объём.")
        return

    side = density['side']
    price_str = density['price']
    qty_str = density['qty']
    usd_total = density['usd']

    print(f"\n🎯 Найдена максимальная плотность:")
    print(f"{side.upper()} | Цена: {price_str} | Объём: {qty_str} | Сумма: ${usd_total:,.2f}")

    # Проверка на стабильность плотности
    survived = True
    for i in range(watch_seconds):
        time.sleep(1)
        snapshot = get_order_book(symbol)
        found = any(
            p == price_str and float(q) >= float(qty_str) * 0.9
            for p, q in snapshot[side]
        )

        print(f"[{i + 1}s] Уровень {'найден' if found else 'исчез'}")

        if not found:
            survived = False
            break

    if survived:
        print(f"\n✅ Плотность удержалась {watch_seconds} секунд.")
        print("🟢 Вероятно реальная.")
    else:
        print(f"\n⚠️ Плотность исчезла за {i + 1} секунд.")
        print("🔴 Возможно spoof (фейковая заявка).")

# Запуск
track_density()
