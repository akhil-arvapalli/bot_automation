import logging

logger = logging.getLogger(__name__)


async def send_telegram_message(update, context, text_content: str):
    """
    Helper to send a message back to the exact chat it came from.
    """
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_content
        )
    except Exception as e:
        logger.error(f"Error sending telegram message: {e}")
