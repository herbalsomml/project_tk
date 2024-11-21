from chaturbate_poller.chaturbate_client import ChaturbateClient
from functions.rate import get_bank_rate, calculate_rates, get_rate_for_amount, get_tokens_rate_text, get_rates_text
from functions.bot import send_message_to_admins
import httpx

class ChaturbateAccountHandler:
    def __init__(self, username, events_token, stats_token, bot, ADMINS, proxies=None):
        self.username = username
        self.events_token = events_token
        self.stats_token = stats_token
        self.bot = bot
        self.proxies = proxies
        self.ADMINS = ADMINS

    async def fetch_token_balance(self):
        """Функция для получения token_balance с использованием прокси."""

        url = f"https://chaturbate.com/statsapi/?username={self.username}&token={self.stats_token}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
                return data.get("token_balance") if data.get("token_balance") else '💀'
        except (httpx.HTTPError, KeyError) as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return '💀'

    async def cb_poller(self):
        async with ChaturbateClient(self.username, self.events_token) as client:
            url = None

            while True:
                response = await client.fetch_events(url)
                for event in response.events:
                    if event.method == "tip":
                        tokens = event.object.tip.tokens
                        user = event.object.user
                        dollars = tokens * 0.05
                        rate = get_bank_rate()
                        rates = calculate_rates(rate)
                        exchange_rate = get_rate_for_amount(rates, dollars)
                        rubles = int(dollars * exchange_rate)

                        exchange_rate = str(exchange_rate).replace(".", ",")

                        text = f"<b>Аккаунт {self.username}</b>\n\n"
                        text += f"<b>💸 <a href='https://chaturbate.com/{user.username}'>{user.username}</a> отправил <code>{tokens}</code> тк.</b>"
                        text += f"\n\n<code>{tokens} {exchange_rate}</code>"
                        text += f"\n\n<code>{rubles}</code>"

                        await send_message_to_admins(self.bot, text, self.ADMINS)
                
                url = str(response.next_url)