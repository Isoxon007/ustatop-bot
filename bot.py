import os
import asyncio
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ========= SOZLAMALAR =========
# Render uchun: TOKEN ni environment variable qilib qo'yish tavsiya qilinadi.
TOKEN = os.getenv("TOKEN") or "8300564206:AAGVFGpqm8RIVyDFQxRXEbQbCkGB4EgblPg"
ADMIN_ID = int(os.getenv("ADMIN_ID") or "8443474178")  

# Yo'nalishlar (reply keyboardda chiqadi)
YONALISHLAR = [
    "Santexnik",
    "Elektrik",
    "Quruvchi (beton/suvoq/devor)",
    "Kafel ustasi",
    "Mebel ustasi",
    "Konditsioner ustasi",
    "Maishiy texnika ustasi",
    "Gaz ustasi",
    "Bo'yoqchi",
    "Gipsokarton ustasi",
    "Tom ustasi",
    "Pol ustasi",
    "Plastik rom / alyumin rom ustasi",
    "Svarchik (payvandchi)",
    "Eshik va zamok ustasi",
    "Oddiy ishchi",
    "Boshqa (o'zim yozaman)",
]

TAJRIBA_VARIANTLAR = [f"{i} yil" for i in range(1, 11)] + ["10+ yil"]

# Hududlar (xohlasang kengaytirasan)
HUDUDLAR = [
    "Namangan shahar",
    "Chortoq",
    "Chust",
    "Kosonsoy",
    "Mingbuloq",
    "Norin",
    "Pop",
    "To'raqo'rg'on",
    "Uychi",
    "Yangiqo'rg'on",
    "Boshqa (o'zim yozaman)",
]


bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ========= STATES =========
class Anketa(StatesGroup):
    ism = State()
    yonalish = State()
    yonalish_custom = State()
    tajriba = State()
    hudud = State()
    hudud_custom = State()
    telefon = State()
    telegram = State()
    tasdiq = State()


# ========= YORDAMCHI FUNKSIYALAR =========
def kb_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Anketa to‘ldirish", callback_data="anketa_start")],
            [InlineKeyboardButton(text="📢 Reklama post yuborish", callback_data="reklama_start")],
        ]
    )

def kb_list(items: list[str], row: int = 2) -> ReplyKeyboardMarkup:
    # ReplyKeyboard uchun tugmalarni qatorlab chiqarish
    buttons = [KeyboardButton(text=x) for x in items]
    keyboard = [buttons[i:i+row] for i in range(0, len(buttons), row)]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def kb_phone_request() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def kb_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="anketa_confirm")],
            [InlineKeyboardButton(text="🔁 Qayta to‘ldirish", callback_data="anketa_restart")],
        ]
    )

def user_identity_line(m: Message) -> str:
    # Adminga kim yuborganini aniq ko'rsatish
    full_name = (m.from_user.full_name or "").strip()
    username = f"@{m.from_user.username}" if m.from_user.username else "(username yo'q)"
    uid = m.from_user.id
    # tg link faqat username bo'lsa
    link = f"https://t.me/{m.from_user.username}" if m.from_user.username else "—"
    return (
        f"👤 Yuboruvchi: {full_name}\n"
        f"🆔 ID: {uid}\n"
        f"💬 Username: {username}\n"
        f"🔗 Profil: {link}"
    )


# ========= START =========
@dp.message(CommandStart())
async def start_handler(message: Message):
    text = (
        "👋 Assalomu alaykum!\n"
        "UstaTop Namangan botiga xush kelibsiz.\n\n"
        "Kerakli bo‘limni tanlang:"
    )
    await message.answer(text, reply_markup=kb_main_menu())


# ========= ANKETA FLOW =========
@dp.callback_query(F.data == "anketa_start")
async def anketa_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Anketa.ism)
    await cb.message.answer("🧑‍🔧 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await cb.answer()

@dp.message(Anketa.ism)
async def anketa_ism(message: Message, state: FSMContext):
    await state.update_data(ism=message.text.strip())
    await state.set_state(Anketa.yonalish)
    await message.answer("🛠 Yo‘nalishingizni tanlang yoki yozib yuboring:", reply_markup=kb_list(YONALISHLAR, row=1))

@dp.message(Anketa.yonalish)
async def anketa_yonalish(message: Message, state: FSMContext):
    txt = message.text.strip()

    if txt == "Boshqa (o'zim yozaman)":
        await state.set_state(Anketa.yonalish_custom)
        await message.answer("✍️ Yo‘nalishingizni yozib yuboring:", reply_markup=ReplyKeyboardRemove())
        return

    # ro'yxatda bo'lmasa ham user yozib yuborsa qabul qilamiz (qulaylik)
    await state.update_data(yonalish=txt)
    await state.set_state(Anketa.tajriba)
    await message.answer("🧠 Tajribangizni tanlang:", reply_markup=kb_list(TAJRIBA_VARIANTLAR, row=3))

@dp.message(Anketa.yonalish_custom)
async def anketa_yonalish_custom(message: Message, state: FSMContext):
    await state.update_data(yonalish=message.text.strip())
    await state.set_state(Anketa.tajriba)
    await message.answer("🧠 Tajribangizni tanlang:", reply_markup=kb_list(TAJRIBA_VARIANTLAR, row=3))

@dp.message(Anketa.tajriba)
async def anketa_tajriba(message: Message, state: FSMContext):
    await state.update_data(tajriba=message.text.strip())
    await state.set_state(Anketa.hudud)
    await message.answer("📍 Hududingizni tanlang:", reply_markup=kb_list(HUDUDLAR, row=2))

@dp.message(Anketa.hudud)
async def anketa_hudud(message: Message, state: FSMContext):
    txt = message.text.strip()

    if txt == "Boshqa (o'zim yozaman)":
        await state.set_state(Anketa.hudud_custom)
        await message.answer("✍️ Hududingizni yozib yuboring:", reply_markup=ReplyKeyboardRemove())
        return

    await state.update_data(hudud=txt)
    await state.set_state(Anketa.telefon)
    await message.answer("📞 Telefon raqamingizni yuboring:", reply_markup=kb_phone_request())

@dp.message(Anketa.hudud_custom)
async def anketa_hudud_custom(message: Message, state: FSMContext):
    await state.update_data(hudud=message.text.strip())
    await state.set_state(Anketa.telefon)
    await message.answer("📞 Telefon raqamingizni yuboring:", reply_markup=kb_phone_request())

@dp.message(Anketa.telefon, F.contact)
async def anketa_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(telefon=phone)
    await state.set_state(Anketa.telegram)
    await message.answer("💬 Telegram username’ingizni yuboring (masalan: @username):", reply_markup=ReplyKeyboardRemove())

@dp.message(Anketa.telefon)
async def anketa_phone_text_fallback(message: Message, state: FSMContext):
    # agar contact tugmasini bosmasa, text kiritsa ham qabul qilamiz
    await state.update_data(telefon=message.text.strip())
    await state.set_state(Anketa.telegram)
    await message.answer("💬 Telegram username’ingizni yuboring (masalan: @username):", reply_markup=ReplyKeyboardRemove())

@dp.message(Anketa.telegram)
async def anketa_telegram(message: Message, state: FSMContext):
    await state.update_data(telegram=message.text.strip())

    data = await state.get_data()
    summary = (
        "📋 Ma’lumotlaringiz:\n\n"
        f"🧑‍🔧 Ism: {data.get('ism','')}\n"
        f"🛠 Yo‘nalish: {data.get('yonalish','')}\n"
        f"🧠 Tajriba: {data.get('tajriba','')}\n"
        f"📍 Hudud: {data.get('hudud','')}\n"
        f"📞 Telefon: {data.get('telefon','')}\n"
        f"💬 Telegram: {data.get('telegram','')}\n\n"
        "Ma’lumotlar to‘g‘rimi?"
    )

    await state.set_state(Anketa.tasdiq)
    await message.answer(summary, reply_markup=kb_confirm())

@dp.callback_query(F.data == "anketa_restart")
async def anketa_restart(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Anketa.ism)
    await cb.message.answer("🔁 Qaytadan boshlaymiz.\n\n🧑‍🔧 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await cb.answer()

@dp.callback_query(F.data == "anketa_confirm")
async def anketa_confirm(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Admin'ga kimdan kelgani ham aniq ko'rinsin:
    sender_info = user_identity_line(cb.message)

    admin_text = (
        "✅ Yangi anketa keldi!\n\n"
        f"{sender_info}\n\n"
        f"🧑‍🔧 Ism: {data.get('ism','')}\n"
        f"🛠 Yo‘nalish: {data.get('yonalish','')}\n"
        f"🧠 Tajriba: {data.get('tajriba','')}\n"
        f"📍 Hudud: {data.get('hudud','')}\n"
        f"📞 Telefon: {data.get('telefon','')}\n"
        f"💬 Telegram: {data.get('telegram','')}"
    )

    await bot.send_message(ADMIN_ID, admin_text)

    await cb.message.answer(
        "✅ Anketangiz qabul qilindi!\n"
        "Admin ko‘rib chiqadi va tez orada kanalga joylanadi. Rahmat!",
        reply_markup=kb_main_menu()
    )
    await state.clear()
    await cb.answer()


# ========= REKLAMA POST FLOW =========
@dp.callback_query(F.data == "reklama_start")
async def reklama_start(cb: CallbackQuery):
    await cb.message.answer(
        "📢 Reklama postingizni yuboring.\n"
        "✅ Rasm/video + tagiga matn (caption) bilan yuborsangiz yaxshi.\n\n"
        "Yuborganingiz adminga yetib boradi.",
        reply_markup=ReplyKeyboardRemove()
    )
    await cb.answer()

@dp.message(F.photo | F.video)
async def reklama_media(message: Message):
    # Media + caption to'liq adminga ketadi (forward bilan)
    await message.forward(ADMIN_ID)

    # Qo'shimcha: kim yuborgani haqida alohida xabar ham yuboramiz
    await bot.send_message(ADMIN_ID, "📌 Reklama post yuboruvchisi:\n\n" + user_identity_line(message))

    await message.answer("✅ Post adminga yuborildi. Rahmat!", reply_markup=kb_main_menu())

@dp.message()
async def fallback(message: Message):
    # Boshqa matnlar kelib qolsa
    await message.answer("ℹ️ /start ni bosing va menyudan tanlang.", reply_markup=kb_main_menu())


# ========= RUN =========
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
