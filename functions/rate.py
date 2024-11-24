import requests
import xml.etree.ElementTree as ET
from constants import CBR_URL, RATE_API_URL
from pprint import pprint

def get_rate():
    try:
        response = requests.get(RATE_API_URL)
        response.raise_for_status()
        data = response.json()
        return data.get("rate_25"), data.get("rate_50"), data.get("rate_100"), data.get("rate_250"), data.get("rate_500")
    except Exception as e:
        return 0, 0, 0, 0, 0


def calculate_rates() -> dict:
    r25, r50, r100, r250, r500 = get_rate()
    return {
        25: r25,
        50: r50,
        100: r100,
        250: r250,
        500: r500,
    }


def get_rate_for_amount(rates: dict, amount: float) -> float:
    for threshold in sorted(rates.keys(), reverse=True):
        if amount >= threshold:
            return rates[threshold]
    return rates[max(rates.keys())]


def get_tokens_rate_text(tokens):
    rates = calculate_rates()
    dollars = tokens * 0.05
    if dollars < 25:
        return "<b>😔 Минимальная сумма к обмену - 500 токенов</b>"
    exchange_rate = get_rate_for_amount(rates, dollars)
    rubles = int(dollars * exchange_rate)
    text = (
            f"<b>💱 Курс для <code>{tokens}</code> тк.</b>\n\n"
            f"<b>💲 За доллар:</b> <code>{exchange_rate}</code> руб.\n"
            f"<b>💳 Вы получите:</b> <code>{rubles}</code> руб.\n"
    )
    return text


def get_rates_text():
    rates = calculate_rates()
    text = (
        f"<b>Минимальная сумма обмена - 25$</b> (500 токенов)\n\n"
        f"<b>Курс за $1:</b>\n"
        + "\n".join([f"<b>от ${k}</b> - <i>{v} руб.</i>" for k, v in rates.items()])
    )

    return text
