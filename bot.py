import telebot
import requests
import json

TOKEN = 'TG_BOT_TOKEN' #это берем у BotFather
token_user = "USER_TOKEN" #токен получается через network с сайта https://rndparking.ru/profile/my-profile , самый последний запрос и будет содержать ваш токен
Car_Number = "А000АА61" #сюда номер машины используя русские буквы



bot = telebot.TeleBot(TOKEN)

parking_status = False  # Статус парковки
ts = None  # Переменная для ID сессии парковки
park_code = ""

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message,
                 "Привет! Я бот для управления парковкой. Используй команды /park для запуска и /stop для остановки.")


@bot.message_handler(commands=['park'])
def park_message(message):
    global parking_status, park_code

    if not parking_status:
        # Запрашиваем номер парковки у пользователя
        bot.reply_to(message, "Пожалуйста, введите номер вашей парковки:")
        # Переключаем состояние для ожидания ввода номера парковки
        bot.register_next_step_handler(message, process_parking_code)
    else:
        bot.reply_to(message, "Парковка уже запущена.")


def process_parking_code(message):
    global park_code, ts  # Добавляем ts в глобальные переменные

    park_code = message.text.strip()  # Сохраняем номер парковки

    # Сначала проверяем, что park_code не пуст
    if park_code:
        url = "https://rndparking.ru/api/payment/start"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://rndparking.ru",
            "priority": "u=1, i",
            "referer": "https://rndparking.ru/profile/parking",
        }

        data = {
            "Vehicle[Number]": f"{Car_Number}", 
            "Vehicle[Category]": "B",
            "Vehicle[NumberFormat]": "rus",
            "Zone": "0001",
            "PaymentService": "balance",
            "Duration": "60", #здесь указывается время в минутах. 60 - 1 час, 10 - 10 минут и тд
            "Token": f"{token_user}", 
            "ParkingCode": f"{park_code}"
        }

        response = requests.post(url, headers=headers, data=data)
        response_checker = requests.get(
            "https://rndparking.ru/api/profile/get-profile-v5?token=423a320b-555b-4b33-9916-6978e0051e90")

        try:
            # Парсим первый уровень ответа (получаем строку с JSON)
            outer_data = json.loads(response_checker.text)
            # Парсим внутренний JSON
            data = json.loads(outer_data)
        except json.JSONDecodeError as e:
            print("Ошибка декодирования JSON:", e)
            data = None

        if data and isinstance(data, dict):
            vehicles = data.get("result", {}).get("Сессии", [])
            for vehicle in vehicles:
                ts = vehicle.get("Номер")

        parking_status = True
        bot.reply_to(message, "Парковка запущена!")

        print(parking_status)
        print(ts)

    else:
        bot.reply_to(message, "Номер парковки не был введен.")


@bot.message_handler(commands=['stop'])
def stop_message(message):
    global parking_status, ts

    print(ts)

    if ts is None:
        bot.reply_to(message, "Сессия парковки не найдена. Возможно, парковка не была запущена.")
        return

    url = "https://rndparking.ru/api/payment/cancel"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://rndparking.ru",
        "priority": "u=1, i",
        "referer": "https://rndparking.ru/profile/parking",
    }

    data = {
        "ReservationId": ts,
        "Token": f"{token_user}"
    }

    response = requests.post(url, headers=headers, data=data)

    parking_status = False
    ts = None  # Сбрасываем сессию
    bot.reply_to(message, "Парковка остановлена!")


if __name__ == '__main__':
    bot.polling()
