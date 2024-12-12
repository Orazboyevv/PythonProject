from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.executor import start_webhook
import logging
import os

# Bot tokeni va kanal ID
TOKEN = "7261655371:AAG7N_5iGguEI-mQ7tmhAhs5MUb6gktkgY8"
CHANNEL_ID = "-1001823396741"

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Bot va dispatcherni ishga tushirish
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Webhook sozlamalari
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 8000))

# So'rovnoma ma'lumotlari
poll_data = {
    1: {"name": "Tibbiyot birlashmasi", "votes": 0},
    2: {"name": "Yoshlar ishlari bo‘limi", "votes": 0},
    3: {"name": "Maktabgacha va maktab ta'limi bo‘limi", "votes": 0},
    4: {"name": "Inson ijtimoiy xizmatlar markazi", "votes": 0},
}

# Ovoz bergan foydalanuvchilarni saqlash
voters = set()

# Inline tugmalarni yaratish
def get_poll_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for key, value in poll_data.items():
        button_text = f"{key}) {value['name']} - {value['votes']}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"vote_{key}"))
    return keyboard

# Foydalanuvchining kanalga a'zo ekanligini tekshirish
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# So‘rovnomani kanalga post qilish
@dp.message_handler(commands=["start_poll"])
async def start_poll(message: types.Message):
    poll_text = (
        "Hurmatli yurtdoshlar,\n"
        "Boyovut tumanidagi ijtimoiy soha tashkilotlaridan qaysi biri 2024-yil davomida namunali tarzda faoliyat olib bordi deb hisoblaysiz?\n\n"
        "✅ So‘rovnomada ishtirok eting, o‘zingiz munosib deb bilgan tashkilotga ovoz bering!"
    )
    poll_keyboard = get_poll_keyboard()
    # Kanalga so‘rovnoma yuborish
    await bot.send_message(chat_id=CHANNEL_ID, text=poll_text, reply_markup=poll_keyboard)
    # Foydalanuvchiga tasdiqlovchi xabar
    await message.answer("So'rovnoma kanalda post qilindi!")

# Ovozni qayta ishlash
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("vote_"))
async def process_vote(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Kanalga a'zo ekanligini tekshirish
    if not await is_subscribed(user_id):
        await bot.answer_callback_query(
            callback_query.id,
            text="Iltimos, avval kanalga a'zo bo'ling!",
            show_alert=True
        )
        return

    # Foydalanuvchining ovoz berganligini tekshirish
    if user_id in voters:
        await bot.answer_callback_query(
            callback_query.id,
            text="Siz avval ovoz bergansiz. Faqat bir marta ovoz berishingiz mumkin!",
            show_alert=True
        )
        return

    # Foydalanuvchining ovozini qayd qilish
    voters.add(user_id)

    # Ovoz hisoblash
    option_id = int(callback_query.data.split("_")[1])
    poll_data[option_id]["votes"] += 1

    # So‘rovnomani yangilash
    updated_text = (
        "Hurmatli yurtdoshlar,\n"
        "Boyovut tumanidagi ijtimoiy soha tashkilotlaridan qaysi biri 2024-yil davomida namunali tarzda faoliyat olib bordi deb hisoblaysiz?\n\n"
        "✅ So‘rovnomada ishtirok eting, o‘zingiz munosib deb bilgan tashkilotga ovoz bering!"
    )
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=updated_text,
        reply_markup=get_poll_keyboard()
    )
    await bot.answer_callback_query(callback_query.id, text="Sizning ovozingiz qabul qilindi!")

# Rasmning file_id sini olish
@dp.message_handler(content_types=['photo'])
async def get_photo_id(message: types.Message):
    # Rasmning file_id sini olish
    photo_id = message.photo[-1].file_id  # Rasmning eng katta hajmli versiyasini tanlash
    await message.answer(f"Rasmning file_id: {photo_id}")

# Webhookni sozlash
async def on_startup(dp):
    logging.info("Webhookni sozlash...")
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logging.info("Webhookni tozalash...")
    await bot.delete_webhook()

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT
    )
