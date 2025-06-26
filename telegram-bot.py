import requests
import time
import threading
import telebot

API_TOKEN = '7685325319:AAEVOGXmVbxux7XQHPmObc12TxMjfZ0ZYMk'
bot = telebot.TeleBot(API_TOKEN)

def get_all_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        data = requests.get(url, timeout=5).json()
        symbols = []
        for s in data['symbols']:
            if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING':
                symbols.append(s['symbol'])
        return symbols
    except Exception as e:
        print(f"Ошибка получения списка символов: {e}")
        return []

SYMBOLS = get_all_symbols()
print(f"Всего символов для мониторинга: {len(SYMBOLS)}")

densities_cache = {}
lock = threading.Lock()  # блокировка для потокобезопасности
THRESHOLD_MULT = 1.5
STABLE_SECONDS = 600  # время "выдержки" плотности для вывода

def get_order_book(symbol='BANUSDT', limit=1000):
    url = 'https://fapi.binance.com/fapi/v1/depth'
    try:
        resp = requests.get(url, params={'symbol': symbol, 'limit': limit}, timeout=5)
        return resp.json()
    except Exception as e:
        print(f"Ошибка получения стакана {symbol}: {e}")
        return None

def get_mark_price(symbol='BANUSDT'):
    url = 'https://fapi.binance.com/fapi/v1/premiumIndex'
    try:
        resp = requests.get(url, params={'symbol': symbol}, timeout=5)
        return float(resp.json()['markPrice'])
    except Exception as e:
        print(f"Ошибка получения цены {symbol}: {e}")
        return None

def get_klines(symbol='BANUSDT', limit=5):
    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {'symbol': symbol, 'interval': '5m', 'limit': limit}
    try:
        resp = requests.get(url, params=params, timeout=5)
        return resp.json()
    except Exception as e:
        print(f"Ошибка получения свечей {symbol}: {e}")
        return []

def get_avg_dollar_volume(symbol='BANUSDT'):
    klines = get_klines(symbol)
    if not klines:
        return None
    volumes = [float(c[4]) * float(c[5]) for c in klines]  # close_price * volume
    return sum(volumes) / len(volumes)

def find_strongest_density(snapshot, avg_volume, mark_price, threshold=1.5):
    densities = []

    for side in ['bids', 'asks']:
        for price_str, qty_str in snapshot.get(side, [])[:500]:
            price = float(price_str)
            qty = float(qty_str)
            total_usd = price * qty

            if total_usd >= avg_volume * threshold:
                densities.append({
                    'side': side,
                    'price': price_str,
                    'qty': qty,
                    'usd': total_usd
                })

    if densities:
        return max(densities, key=lambda d: d['usd'])
    return None

def monitor_densities():
    while True:
        now = time.time()
        for symbol in SYMBOLS:
            avg_volume = get_avg_dollar_volume(symbol)
            mark_price = get_mark_price(symbol)
            if avg_volume is None or mark_price is None:
                continue

            snapshot = get_order_book(symbol)
            if not snapshot:
                continue

            density = find_strongest_density(snapshot, avg_volume, mark_price, threshold=THRESHOLD_MULT)

            with lock:
                if symbol not in densities_cache:
                    densities_cache[symbol] = {}

                if density:
                    old = densities_cache[symbol].get('density')
                    if old and old['price'] == density['price'] and old['side'] == density['side']:
                        density['start_time'] = old['start_time']
                    else:
                        density['start_time'] = now

                    densities_cache[symbol]['density'] = density
                else:
                    densities_cache[symbol]['density'] = None

        time.sleep(3)

def format_density_report():
    report_lines = []
    now = time.time()
    with lock:
        items = list(densities_cache.items())

    for symbol, data in items:
        density = data.get('density')
        if density:
            lifetime_sec = now - density['start_time']
            if lifetime_sec >= STABLE_SECONDS:
                mark_price = get_mark_price(symbol)
                if mark_price is None:
                    continue

                distance = abs(float(density['price']) - mark_price) / mark_price * 100
                if distance > 7:  # Фильтр: расстояние не больше 7%
                    continue

                order_type = 'Покупка' if density['side'] == 'bids' else 'Продажа'

                line = (
                    f"<b>{symbol}</b>\n\n"
                    f"Плотность на цене: <b>{density['price']}$</b>\n"
                    f"Сумма: <b>{density['usd'] / 1000:.1f}K$</b>\n"
                    f"Расстояние: <b>{distance:.2f}%</b>\n"
                    f"Время жизни: <b>{lifetime_sec / 60:.1f} мин</b>\n"
                    f"Тип ордера: <b>{order_type}</b>\n"
                )
                report_lines.append(line)

    if not report_lines:
        return "❌ <b>На данный момент устойчивых плотностей нет.</b>"

    return "<b>📊 Актуальные плотности:</b>\n\n" + "\n".join(report_lines)



@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я мониторю плотности по монетам. Используй команду /densities чтобы увидеть актуальные.")


MAX_MESSAGE_LENGTH = 4000  # с запасом, чтобы не превышать лимит

def send_long_message(bot, chat_id, text, parse_mode=None):
    if len(text) <= MAX_MESSAGE_LENGTH:
        bot.send_message(chat_id, text, parse_mode=parse_mode)
    else:
        # разбиваем по строкам
        lines = text.split('\n')
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH:
                bot.send_message(chat_id, chunk, parse_mode=parse_mode)
                chunk = ""
            chunk += line + "\n"
        if chunk:
            bot.send_message(chat_id, chunk, parse_mode=parse_mode)

@bot.message_handler(commands=['densities'])
def handle_densities(message):
    report = format_density_report()
    send_long_message(bot, message.chat.id, report, parse_mode='HTML')



if __name__ == '__main__':
    monitor_thread = threading.Thread(target=monitor_densities, daemon=True)
    monitor_thread.start()

    print("Бот запущен...")
    bot.infinity_polling()
