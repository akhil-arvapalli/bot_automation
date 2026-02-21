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
        response_text = process_message(chat_id, text)

        if not response_text:
            logger.info("-> Rules didn't match. Routing to AI...")
            response_text = get_ai_response(text)
        else:
            logger.info("-> Rule matched! Response generated.")

        await send_telegram_message(update, context, response_text)

    except Exception as err:
        logger.error(f"Error processing message: {err}")
        await send_telegram_message(update, context, "An error occurred. Please try again later.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages — used for ID uploads during KYC."""
    chat_id = str(update.effective_chat.id)
    caption = update.message.caption or ""

    logger.info(f"--- Received PHOTO from {chat_id} ---")
    logger.info(f"Caption: {caption}")

    try:
        # Pass a special marker so rule_engine knows it's a photo
        response_text = process_message(chat_id, "[PHOTO_RECEIVED]")

        if not response_text:
            response_text = "Thanks for the image! How can I help you?"

        await send_telegram_message(update, context, response_text)

    except Exception as err:
        logger.error(f"Error processing photo: {err}")
        await send_telegram_message(update, context, "An error occurred. Please try again later.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads — also used for ID scans."""
    chat_id = str(update.effective_chat.id)

    logger.info(f"--- Received DOCUMENT from {chat_id} ---")

    try:
        response_text = process_message(chat_id, "[PHOTO_RECEIVED]")

        if not response_text:
            response_text = "Thanks for the document! How can I help you?"

        await send_telegram_message(update, context, response_text)

    except Exception as err:
        logger.error(f"Error processing document: {err}")
        await send_telegram_message(update, context, "An error occurred. Please try again later.")


if __name__ == '__main__':
    if not config.TELEGRAM_TOKEN or config.TELEGRAM_TOKEN == 'your_telegram_bot_token_here':
        logger.error("Please set TELEGRAM_TOKEN in your .env file.")
        exit(1)

    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    # Handle text messages (not commands)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Handle photo uploads (for KYC ID)
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Handle document uploads (for KYC ID scans/PDFs)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Telegram Bot is up and running!")
    application.run_polling()
