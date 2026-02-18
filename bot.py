import os
import re
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. Koyeb Variables ga BOT_TOKEN qo‘ying.")
if ADMIN_ID == 0:
    raise RuntimeError("ADMIN_ID topilmadi. Koyeb Variables ga ADMIN_ID qo‘ying.")

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- Ma'lumotlar ---
DIRECTIONS = [
    "Santexnik", "Elektrik", "Gaz usta", "Konditsioner usta", "Mebel usta",
    "Qurilish usta", "Kafel ustasi", "Bo'yoqchi", "Texnika ustasi",
    "Payvandchi", "Tom ustasi", "Gipsokarton usta", "Oddiy ishchi", "Boshqa"
]

EXPERIENCE = [f"{i} yil" for i in range(1, 11)] + ["10+ yil"]

DISTRICTS = [
    "Namangan shahar",
    "Mingbuloq tumani", "Norin tumani", "Uychi tumani", "Chortoq tumani",
    "Chust tumani", "Kosonsoy tumani", "Pop tumani", "To'raqo'rg'on tumani",
    "Yangiqo'rg'on tumani", "Davlatobod tumani"
]

def chunks(items, n=2):
    out = []
    row = []
    for x in items:
        row.append(x)
        if len(row) == n:
            out.append(row)
            row = []
    if row:
        out.append(row)
    return out

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Anketa to‘ldirish", callback_data="anketa")],
        [InlineKeyboardButton(text="📢 Reklama post yuborish", callback_data="reklama")]
    ])

def direction_kb():
    return ReplyKeyboardMarkup(
        keyboard=chunks([KeyboardButton(text=x) for x in DIRECTIONS], 2),
        resize_keyboard=True,
        one_time_keyboard=True
    )

def experience_kb():
    return ReplyKeyboardMarkup(
        keyboard=chunks([KeyboardButton(text=x) for x in EXPERIENCE], 3),
        resize_keyboard=True,
        one_time_keyboard=True
    )

def district_kb():
    return ReplyKeyboardMarkup(
        keyboard=chunks([KeyboardButton(text=x) for x in DISTRICTS], 2),
        resize_keyboard=True,
        one_time_keyboard=True
    )

def skip_kb(text="➡️ Keyingisi"):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm")],
        [InlineKeyboardButton(text="✏️ Tahrirlash (qayta)", callback_data="restart")]
    ])

# --- FSM ---
class Form(StatesGroup):
    name = State()
    direction = State()
    experience = State()
    skills_optional = State()
    district = State()
    phone = State()
    telegram = State()
    photos_optional = State()
    confirm = State()

class AdPost(StatesGroup):
    waiting_post = State()

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "UstaTop Namangan botiga xush kelibsiz.\n"
        "Bot orqali anketa to‘ldirishingiz yoki reklama postingizni yuborishingiz mumkin.\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=main_menu_kb()
    )

# --- MENU callbacks ---
@dp.callback_query(F.data == "anketa")
async def cb_anketa(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("🧑‍🔧 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.name)
    await call.answer()

@dp.callback_query(F.data == "reklama")
async def cb_reklama(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "📢 Reklama postingizni yuboring.\n"
        "Rasm/video + tagiga matn (caption) bo‘lsa, hammasini birga yuboring.\n\n"
        "✅ Yuborganingiz adminga boradi.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdPost.waiting_post)
    await call.answer()

# --- анкета flow ---
@dp.message(Form.name)
async def f_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2:
        return await message.answer("Iltimos, ismingizni to‘g‘ri kiriting.")
    await state.update_data(name=name)
    await message.answer("🛠 Yo‘nalishingizni tanlang:", reply_markup=direction_kb())
    await state.set_state(Form.direction)

@dp.message(Form.direction)
async def f_direction(message: Message, state: FSMContext):
    t = (message.text or "").strip()
    if t not in DIRECTIONS:
        return await message.answer("Ro‘yxatdan tanlang:", reply_markup=direction_kb())
    await state.update_data(direction=t)
    await message.answer("🧠 Tajribangizni tanlang:", reply_markup=experience_kb())
    await state.set_state(Form.experience)

@dp.message(Form.experience)
async def f_experience(message: Message, state: FSMContext):
    t = (message.text or "").strip()
    if t not in EXPERIENCE:
        return await message.answer("Ro‘yxatdan tanlang:", reply_markup=experience_kb())
    await state.update_data(experience=t)
    await message.answer(
        "🧰 Bu sohada nimalar qila olasiz? (ixtiyoriy)\n"
        "Masalan: quvur almashtirish, radiator ulash, montaj...\n\n"
        "O‘tkazib yuborish uchun ➡️ Keyingisi bosing.",
        reply_markup=skip_kb()
    )
    await state.set_state(Form.skills_optional)

@dp.message(Form.skills_optional)
async def f_skills(message: Message, state: FSMContext):
    t = (message.text or "").strip()
    skills = "" if t == "➡️ Keyingisi" else t
    await state.update_data(skills=skills)
    await message.answer("📍 Hududingizni tanlang:", reply_markup=district_kb())
    await state.set_state(Form.district)

@dp.message(Form.district)
async def f_district(message: Message, state: FSMContext):
    t = (message.text or "").strip()
    if t not in DISTRICTS:
        return await message.answer("Ro‘yxatdan tanlang:", reply_markup=district_kb())
    await state.update_data(district=t)
    await message.answer("📞 Telefon raqamingizni yuboring:", reply_markup=phone_kb())
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def f_phone(message: Message, state: FSMContext):
    phone = None
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    else:
        # text bo'lsa ham qabul qilamiz (lekin tekshiramiz)
        t = (message.text or "").strip()
        t = re.sub(r"[^\d+]", "", t)
        if len(t) >= 9:
            phone = t

    if not phone:
        return await message.answer("Raqamni tugma orqali yuboring yoki to‘g‘ri raqam kiriting.", reply_markup=phone_kb())

    await state.update_data(phone=phone)
    await message.answer("💬 Telegram username’ingizni yuboring (masalan: @username):", reply_markup=skip_kb())
    await state.set_state(Form.telegram)

@dp.message(Form.telegram)
async def f_telegram(message: Message, state: FSMContext):
    t = (message.text or "").strip()
    tg = "" if t == "➡️ Keyingisi" else t
    if tg and not tg.startswith("@"):
        tg = "@" + tg
    await state.update_data(telegram=tg)

    await message.answer(
        "🖼 Ish rasmlarini yuborishingiz mumkin (ixtiyoriy).\n"
        "1-5 ta rasm yuboring. Tugatgach ➡️ Keyingisi bosing.",
        reply_markup=skip_kb()
    )
    await state.update_data(photos=[])
    await state.set_state(Form.photos_optional)

@dp.message(Form.photos_optional)
async def f_photos(message: Message, state: FSMContext):
    if (message.text or "").strip() == "➡️ Keyingisi":
        data = await state.get_data()
        # summary
        s = (
            "📝 <b>Anketa ma'lumotlari</b>\n\n"
            f"🧑‍🔧 Ism: <b>{data.get('name','')}</b>\n"
            f"🛠 Yo‘nalish: <b>{data.get('direction','')}</b>\n"
            f"🧠 Tajriba: <b>{data.get('experience','')}</b>\n"
            f"🧰 Nimalar qila oladi: <b>{data.get('skills','') or '—'}</b>\n"
            f"📍 Hudud: <b>{data.get('district','')}</b>\n"
            f"📞 Telefon: <b>{data.get('phone','')}</b>\n"
            f"💬 Telegram: <b>{data.get('telegram','') or '—'}</b>\n"
            f"🖼 Ish rasmlari: <b>{len(data.get('photos', []))} ta</b>\n"
        )
        await message.answer(s, reply_markup=confirm_kb())
        await state.set_state(Form.confirm)
        return

    photos = (await state.get_data()).get("photos", [])
    if message.photo:
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)
        if len(photos) >= 5:
            await message.answer("✅ 5 ta rasm qabul qilindi. Endi ➡️ Keyingisi bosing.", reply_markup=skip_kb())
        else:
            await message.answer(f"✅ Rasm qabul qilindi ({len(photos)}/5). Yana yuboring yoki ➡️ Keyingisi bosing.", reply_markup=skip_kb())
    else:
        await message.answer("Faqat rasm yuboring yoki ➡️ Keyingisi bosing.", reply_markup=skip_kb())

@dp.callback_query(Form.confirm, F.data == "restart")
async def cb_restart(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Qaytadan boshlaymiz. 🧑‍🔧 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.name)
    await call.answer()

@dp.callback_query(Form.confirm, F.data == "confirm")
async def cb_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    user = call.from_user
    who = (
        f"👤 <b>Kimdan:</b> {user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"🔗 <b>Username:</b> @{user.username}" if user.username else f"👤 <b>Kimdan:</b> {user.full_name}\n🆔 <b>ID:</b> <code>{user.id}</code>\n🔗 <b>Username:</b> —"
    )

    admin_text = (
        "🆕 <b>Yangi anketa keldi ✅</b>\n\n"
        f"{who}\n\n"
        f"🧑‍🔧 Ism: <b>{data.get('name','')}</b>\n"
        f"🛠 Yo‘nalish: <b>{data.get('direction','')}</b>\n"
        f"🧠 Tajriba: <b>{data.get('experience','')}</b>\n"
        f"🧰 Nimalar qila oladi: <b>{data.get('skills','') or '—'}</b>\n"
        f"📍 Hudud: <b>{data.get('district','')}</b>\n"
        f"📞 Telefon: <b>{data.get('phone','')}</b>\n"
        f"💬 Telegram: <b>{data.get('telegram','') or '—'}</b>\n"
        f"🖼 Ish rasmlari: <b>{len(data.get('photos', []))} ta</b>\n"
    )

    # adminga yuborish
    await bot.send_message(ADMIN_ID, admin_text)

    # rasm bo'lsa yuboramiz
    for fid in data.get("photos", []):
        await bot.send_photo(ADMIN_ID, fid)

    await call.message.answer(
        "✅ Anketangiz qabul qilindi.\nTez orada kanalga joylanadi. Rahmat!",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    await call.answer()

# --- reklama post ---
@dp.message(AdPost.waiting_post)
async def ad_post(message: Message, state: FSMContext):
    user = message.from_user
    header = f"📢 <b>Yangi reklama post keldi</b>\n👤 {user.full_name} | 🆔 <code>{user.id}</code>"
    if user.username:
        header += f" | @{user.username}"

    # Matn bo‘lsa ham yuboramiz
    if message.content_type == ContentType.TEXT:
        await bot.send_message(ADMIN_ID, header + "\n\n" + message.text)
        await message.answer("✅ Qabul qilindi. Admin ko‘rib chiqadi.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    # Media bo‘lsa: caption + media birga adminga boradi
    await bot.send_message(ADMIN_ID, header)

    try:
        await bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception:
        # fallback: forward
        await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

    await message.answer("✅ Qabul qilindi. Admin ko‘rib chiqadi.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

# --- Run ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


