import logging
import os

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import database
import bot_func

# Определяем, используем ли мы токен для тестирования (debug)
debug = 1  # Установите на 0, если вы хотите использовать основной токен

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Определяем имя файла с токеном в зависимости от переменной debug
token_filename = 'test_token.txt' if debug else 'main_token.txt'

# Проверяем, существует ли файл с токеном
if not os.path.isfile(token_filename):
    raise FileNotFoundError(f"Файл {token_filename} не найден.")

# Читаем токен из файла
with open(token_filename, 'r') as file:
    TOKEN = file.read().strip()


def main() -> None:
    # Перед использованием базы данных, убедитесь, что таблица создана
    database.create_user_table()

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on non command i.e. message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_func.echo))

    application.add_handler(CommandHandler("start", bot_func.start))
    application.add_handler(CallbackQueryHandler(bot_func.button))
    application.add_handler(CommandHandler("help", bot_func.help_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
