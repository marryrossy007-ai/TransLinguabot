import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import Conflict
from deep_translator import GoogleTranslator

TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TOKEN:
    print("=" * 60)
    print("❌ ERROR: TELEGRAM_TOKEN environment variable not set!")
    print("📝 Please add it in Railway Dashboard:")
    print("   Variables → Add Variable → TELEGRAM_TOKEN = your_token")
    print("=" * 60)
    raise ValueError("TELEGRAM_TOKEN environment variable not set!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "chinese": "zh-CN",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "hindi": "hi",
    "dutch": "nl",
    "greek": "el",
    "turkish": "tr"
}

def get_language_keyboard():
    buttons = []
    row = []
    for i, (name, code) in enumerate(SUPPORTED_LANGUAGES.items()):
        display_name = name.capitalize()
        row.append(InlineKeyboardButton(display_name, callback_data=f"lang_{code}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🌍 Change Language", callback_data="change_lang")],
        [InlineKeyboardButton("📖 Current Language", callback_data="current_lang")],
        [InlineKeyboardButton("🆘 Help", callback_data="help_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def translate_text(text: str, target_lang: str) -> str:
    try:
        translator = GoogleTranslator(target=target_lang)
        return translator.translate(text)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise e

def get_lang_name(lang_code: str) -> str:
    for name, code in SUPPORTED_LANGUAGES.items():
        if code == lang_code:
            return name
    return "unknown"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "target_lang" not in context.user_data:
        context.user_data["target_lang"] = "es"
    
    current_lang_name = get_lang_name(context.user_data["target_lang"])
    
    welcome_text = (
        f"🌍 Welcome to TransLinguabot!\n\n"
        "I can translate your messages to different languages.\n\n"
        "📤 **How to use:**\n"
        "1. Send me any text message\n"
        "2. I'll translate it to your selected language\n"
        "3. Use the menu to change languages\n\n"
        f"🔹 **Current target language:** {current_lang_name.capitalize()}\n\n"
        "🔽 **Use the menu below to get started!**"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 **TransLinguabot Help**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/lang - Change target language\n"
        "/info - View current settings\n\n"
        "**How it works:**\n"
        "1. Send any text message\n"
        "2. The bot translates it to your chosen language\n"
        "3. Use /lang to change the target language"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_lang = context.user_data.get("target_lang", "es")
    current_name = get_lang_name(current_lang)
    await update.message.reply_text(
        f"🌍 **Current target language:** {current_name.capitalize()}\n\n"
        "Choose a new target language:",
        parse_mode="Markdown",
        reply_markup=get_language_keyboard()
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_lang = context.user_data.get("target_lang", "es")
    current_name = get_lang_name(current_lang)
    info_text = (
        f"📊 **Your Settings**\n\n"
        f"🌍 **Target Language:** {current_name.capitalize()}\n"
        "Send any text to translate it!"
    )
    await update.message.reply_text(info_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_lang = context.user_data.get("target_lang", "es")
        text = update.message.text
        
        if text.startswith('/'):
            return
        
        await update.message.chat.send_action(action="typing")
        
        translated = translate_text(text, target_lang)
        lang_name = get_lang_name(target_lang)
        
        await update.message.reply_text(
            f"🌍 **Translation ({lang_name.capitalize()}):**\n\n{translated}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Message handler error: {e}")
        await update.message.reply_text("❌ Failed to translate your message. Please try again.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return
    
    if data == "change_lang":
        current_lang = context.user_data.get("target_lang", "es")
        current_name = get_lang_name(current_lang)
        await query.edit_message_text(
            f"🌍 **Current target language:** {current_name.capitalize()}\n\n"
            "Choose a new target language:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard()
        )
        return
    
    if data == "current_lang":
        current_lang = context.user_data.get("target_lang", "es")
        current_name = get_lang_name(current_lang)
        await query.edit_message_text(
            f"🌍 **Your current target language is:** {current_name.capitalize()}\n\n"
            "Use the button below to change it:",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return
    
    if data == "help_menu":
        help_text = (
            "🆘 **How to use the bot:**\n\n"
            "1. Send any text message\n"
            "2. I'll translate it to your chosen language\n"
            "3. Use the menu to change languages\n\n"
            "**Commands:**\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/lang - Change target language\n"
            "/info - View current settings"
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=get_main_menu())
        return
    
    if data.startswith("lang_"):
        lang_code = data.replace("lang_", "")
        lang_name = get_lang_name(lang_code)
        
        if lang_name == "unknown":
            await query.edit_message_text("❌ Invalid language selected.")
            return
        
        context.user_data["target_lang"] = lang_code
        
        await query.edit_message_text(
            f"✅ Language changed to: **{lang_name.capitalize()}**\n\n"
            "Send any text to translate it to this language!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

async def main():
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("lang", lang_command))
        application.add_handler(CommandHandler("info", info_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_error_handler(error_handler)

        logger.info("🔄 Clearing any existing webhook...")
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook cleared successfully!")

        logger.info("🚀 Starting TransLinguabot...")
        logger.info(f"✅ Bot is running on Python {os.sys.version}")

        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        while True:
            await asyncio.sleep(1)

    except Conflict as e:
        logger.error(f"❌ Conflict error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
