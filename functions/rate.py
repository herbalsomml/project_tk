import requests
import xml.etree.ElementTree as ET
from constants import CBR_URL


def get_bank_rate() -> float:
    try:
        response = requests.get(CBR_URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        value = root.find(".//Valute[@ID='R01235']/Value").text
        return float(value.replace(',', '.'))
    except Exception as e:
        return 0.0


def calculate_rates(base_rate: float) -> dict:
    return {
        25: round(base_rate * 0.92, 2),
        50: round(base_rate * 0.93, 2),
        100: round(base_rate * 0.945, 2),
        250: round(base_rate * 0.96, 2),
        500: round(base_rate * 0.97, 2),
    }


def get_rate_for_amount(rates: dict, amount: float) -> float:
    for threshold in sorted(rates.keys()):
        if amount < threshold:
            return rates[threshold]
    return rates[max(rates.keys())]


def get_tokens_rate_text(tokens):
    rate = get_bank_rate()
    rates = calculate_rates(rate)
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
    rate = get_bank_rate()
    rates = calculate_rates(rate)
    text = (
        f"<b>Минимальная сумма обмена - 25$</b> (500 токенов)\n\n"
        f"<b>Курс за $1:</b>\n"
        + "\n".join([f"<b>от ${k}</b> - <i>{v} руб.</i>" for k, v in rates.items()])
    )

    return text