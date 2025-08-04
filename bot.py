import os
import logging
import asyncio
import datetime
import jdatetime

from telegram import Update, Message
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# تنظیم توکن از متغیر محیطی
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# آیدی مدیر (فقط پاسخ‌های ویس ارسالی او پذیرفته می‌شود)
ADMIN_ID = 328462927  # دکتر زجاجی

# شناسه گروه هدف برای انتشار پست‌ها
GROUP_ID = -1001700701292

# ذخیره‌سازی پیام‌های متنی برای تطبیق با ویس
pending_questions = {}

# پیکربندی لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# استخراج هشتگ‌ها از متن
def extract_hashtags(text):
    return [word for word in text.split() if word.startswith("#")]

# تابع هندل پیام‌های متنی
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return

    if update.effective_chat.id == GROUP_ID:
        pending_questions[message.message_id] = {
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "name": message.from_user.full_name,
            "text": message.text,
            "date": message.date,
        }

# تابع هندل ویس دکتر
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.voice or not message.reply_to_message:
        return

    if update.effective_user.id != ADMIN_ID:
        return  # فقط دکتر مجاز است

    original = message.reply_to_message
    question = pending_questions.get(original.message_id)

    if not question:
        return

    # اطلاعات کاربر سوال‌کننده
    username = question["username"]
    name = question["name"]
    text = question["text"]
    date = jdatetime.datetime.fromgregorian(datetime=question["date"]).strftime("%Y/%m/%d")
    hashtags = extract_hashtags(text)
    hashtags.append("#مشاوره_دارویی")
    hashtags_text = " ".join(hashtags)

    # کپشن نهایی
    caption = (
        f"🗣 سوال توسط {'@'+username if username else name}:\n"
        f"❓ {text}\n\n"
        f"🎧 پاسخ دکتر زجاجی:\n"
        f"📅 تاریخ: {date}\n"
        f"{hashtags_text}"
    )

    await context.bot.copy_message(
        chat_id=GROUP_ID,
        from_chat_id=message.chat_id,
        message_id=message.message_id,
        caption=caption,
        parse_mode="HTML"
    )

    # حذف از لیست سوال‌های در انتظار
    del pending_questions[original.message_id]

# تابع اصلی برای راه‌اندازی بات
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(GROUP_ID), handle_text))
    app.add_handler(MessageHandler(filters.VOICE & filters.Chat(GROUP_ID), handle_voice))

    print("🤖 ربات در حال اجراست...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
