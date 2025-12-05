"""
Notificador de Telegram para alertas de disponibilidad
"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

    def is_configured(self) -> bool:
        """Verifica si el bot está configurado correctamente."""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Envía mensaje de forma síncrona."""
        if not self.is_configured():
            print("⚠️ Telegram no configurado. Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")
            return False

        async def _send():
            bot = Bot(token=self.bot_token)
            try:
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
                return True
            except TelegramError as e:
                print(f"Error enviando mensaje Telegram: {e}")
                return False
            finally:
                await bot.close()

        try:
            # Crear nuevo event loop si es necesario
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(_send())
        except Exception as e:
            print(f"Error enviando mensaje Telegram: {e}")
            return False

    def send_availability_alert(self, availability_data: dict) -> bool:
        """
        Envía alerta de disponibilidad.

        Args:
            availability_data: dict con fechas y productos disponibles
                {
                    'DD/MM/YYYY': [
                        {'id': 123, 'name': 'Producto', 'availability': 'AVAILABLE', ...},
                        ...
                    ]
                }
        """
        if not availability_data:
            return False

        message = "🎫 <b>¡DISPONIBILIDAD DETECTADA!</b>\n"
        message += "🏛️ Museos Vaticanos\n\n"

        for date, products in availability_data.items():
            message += f"📅 <b>{date}</b>\n"
            for product in products:
                status_icon = "✅" if product.get('availability') == 'AVAILABLE' else "⚠️"
                name = product.get('name', 'N/A')[:50]
                message += f"  {status_icon} {name}\n"
            message += "\n"

        message += "🔗 <a href='https://tickets.museivaticani.va/home/calendar/visit/MV-Biglietti'>Reservar ahora</a>"

        return self.send_message(message)

    def send_status_update(self, message: str) -> bool:
        """Envía actualización de estado."""
        return self.send_message(f"ℹ️ {message}")

    def send_error_alert(self, error: str) -> bool:
        """Envía alerta de error."""
        return self.send_message(f"❌ <b>Error:</b> {error}")


# Test
if __name__ == '__main__':
    notifier = TelegramNotifier()

    if notifier.is_configured():
        print("Bot configurado. Enviando mensaje de prueba...")
        success = notifier.send_message("🧪 Test de conexión - Vatican Ticket Monitor")
        print(f"Mensaje enviado: {success}")
    else:
        print("Bot no configurado.")
        print("1. Crea un bot con @BotFather en Telegram")
        print("2. Obtén tu chat_id enviando un mensaje a @userinfobot")
        print("3. Configura las variables en .env:")
        print("   TELEGRAM_BOT_TOKEN=tu_token")
        print("   TELEGRAM_CHAT_ID=tu_chat_id")
