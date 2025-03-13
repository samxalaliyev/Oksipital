import io
import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Konuşma durumu sabiti
SELECT_MODEL = 0

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Kullanıcının gönderdiği prompt'u alıp model seçimi için inline butonları gösteren giriş fonksiyonu
async def handle_prompt(update: Update, context: CallbackContext) -> int:
    prompt = update.message.text
    context.user_data['prompt'] = prompt
    keyboard = [
        [InlineKeyboardButton("Flux", callback_data="flux")],
        [InlineKeyboardButton("SDXL", callback_data="sdxl")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Lütfen bir model seçin:", reply_markup=reply_markup)
    return SELECT_MODEL

# Inline butonlardan model seçildiğinde çalışacak fonksiyon
async def select_model(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    selected_model = query.data
    prompt = context.user_data.get('prompt')
    if not prompt:
        await query.edit_message_text("Prompt bulunamadı, lütfen tekrar deneyin.")
        return ConversationHandler.END
    await query.edit_message_text(f"Seçilen model: {selected_model.upper()}\nGörsel oluşturuluyor, lütfen bekleyin...")

    # Cloudflare Worker API endpoint'iniz
    WORKER_ENDPOINT = "https://ai-text-to-image.yenitest.workers.dev/"
    payload = {"prompt": prompt, "model": selected_model}
    
    try:
        response = requests.post(WORKER_ENDPOINT, json=payload)
        if response.status_code == 200:
            image_bytes = response.content
            bio = io.BytesIO(image_bytes)
            bio.name = "generated.jpg"
            await query.message.reply_photo(photo=bio)
        else:
            await query.message.reply_text(f"API hatası: {response.status_code}\n{response.text}")
    except Exception as e:
        logger.error(f"API isteği sırasında hata: {e}")
        await query.message.reply_text(f"Hata oluştu: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)],
        states={
            SELECT_MODEL: [CallbackQueryHandler(select_model)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)]
    )

    app.add_handler(conv_handler)
    logger.info("🚀 Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()


  
