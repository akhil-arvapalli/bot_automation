import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

import config
from routing.rule_engine import process_message
from services.conversation_ai import get_ai_response
from responses.handlers import send_telegram_message

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text

    if not text:
        return

    logger.info(f"--- Received message from {chat_id} ---")
    logger.info(f"Text: {text}")

    try:
        # 1. Rule Engine execution First
        response_text = process_message(chat_id, text)

        # 2. AI Fallback if rules don't match
        if not response_text:
            logger.info("-> Rules didn't match. Routing to AI...")
            response_text = get_ai_response(text)
        else:
            logger.info("-> Rule matched! Response generated.")

        # 3. Send Response
        await send_telegram_message(update, context, response_text)

    except Exception as err:
        logger.error(f"Error processing message: {err}")
        await send_telegram_message(update, context, "An error occurred. Please try again later.")


if __name__ == '__main__':
    if not config.TELEGRAM_TOKEN or config.TELEGRAM_TOKEN == 'your_telegram_bot_token_here':
        logger.error("Please set TELEGRAM_TOKEN in your .env file.")
        exit(1)

    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    # Handle all text messages that are not commands
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Telegram Bot is up and running!")
    application.run_polling()
