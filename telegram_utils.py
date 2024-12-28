from telegram import Bot
from multicam_app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

async def get_telegram_bot():
    """
    Returns a telegram.Bot instance initialized with the token from config.
    """
    return Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_message(bot, chat_id, text, logger=None):
    """
    Sends a text message to a specified Telegram chat ID.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        if logger:
            logger.info(f"Sent Telegram message: {text}")
    except Exception as ex:
        if logger:
            logger.exception(f"Failed to send Telegram message: {ex}")

async def send_telegram_alert(
    bot=None, 
    chat_id=TELEGRAM_CHAT_ID, 
    photo_path=None, 
    caption="", 
    logger=None
):
    if bot is None:
        bot = await get_telegram_bot()

    try:
        with open(photo_path, 'rb') as photo_file:
            await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=caption)
        if logger:
            logger.info(f"Telegram alert sent successfully for {photo_path}")
    except Exception as e:
        if logger:
            logger.exception(f"Failed to send Telegram alert. Error: {str(e)}")


