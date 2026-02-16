import os
import asyncio
from typing import List, Optional

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
# Render uchun TOKEN va ADMIN_ID ni Environment Variables qilib qo'yish tavsiya qilinadi.
TOKEN = os.getenv("TOKEN") or "8300564206:AAF_NuOYrHZw8p2X1Otu0mID1eoJM_rRm8k"
ADMIN_ID = int(os.getenv("ADMIN_ID") or "8443474178")  


bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ========= RO'YXATLAR =========
YONALISHLAR = [
    "Santexnik",
    "Elektrik",
    "Gaz ustasi",
    "Konditsioner ustasi",
    "Mebel ustasi",
    "Qurilish ustasi",
    "Kafel ustasi",
    "Bo'yoqchi",
    "Maishiy texnika ustasi",
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

HUDUDLAR = [
    "Namangan shahri",
    "Chortoq tumani",
    "Chust tumani",
    "Kosonsoy tumani",
    "Mingbuloq tumani",
    "Norin tumani",
    "Pop tumani",
    "To‘raqo‘rg‘on tumani",
    "Uychi tumani",
    "Yangiqo‘rg‘on tumani",
    "Boshqa (o'zim yozaman)",
]


# ========= STATES =========
class Anketa(StatesGroup):
    ism = State()
    yonalish = State()
    yonalish_custom = State()
    tajriba = State()
    ishlar = State()          # ixtiyoriy
    hudud = State()
    hudud_custom = State()
    telefon = State()
    telegram = State()
    rasmlar = State()         # ixtiyoriy (bir nechta rasm)
    tasdiq = State()


# ========= KEYBOARDS =========
def kb_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Anketa to‘ldirish", callback_data="anketa_start")],
            [InlineKeyboardButton(text="📢 Reklama post yuborish", callback_data="reklama_start")],
        ]
    )

def kb_list(items: List[str], row: int = 2) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text=x) for x in items]
    keyboard = [buttons[i:i+row] for i in range(0, len(buttons), row)]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def kb_phone_request() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def kb_skip_next(text_btn: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text_btn)]],
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


# ========= YORDAMCHI =========
def identity_from_user(user) -> str:
    full_name = (user.full_name or "").strip()
    username = f"@{user.username}" if user.username else "(username yo'q)"
    uid = user.id
    link = f"https://t.me/{user.username}" if user.username else "—"
    return (
        f"👤 Yuboruvchi: {full_name}\n"
        f"🆔 ID: {uid}\n"
        f"💬 Username: {username}\n"
        f"🔗 Profil: {link}"
    )

async def send_admin_anketa(user, data: dict):
    # Adminga anketa yuborish (matn + rasmlar bo'lsa)
    admin_text = (
        "✅ Yangi anketa keldi!\n\n"
        f"{identity_from_user(user)}\n\n"
        f"🧑‍🔧 Ism: {data.get('ism','')}\n"
        f"🛠 Yo‘nalish: {data.get('yonalish','')}\n"
        f"🧠 Tajriba: {data.get('tajriba','')}\n"
        f"🧰 Nimalar qila oladi: {data.get('ishlar','Ko‘rsatilmagan')}\n"
        f"📍 Hudud: {data.get('hudud','')}\n"
        f"📞 Telefon: {data.get('telefon','')}\n"
        f"💬 Telegram: {data.get('telegram','')}\n"
    )

    await bot.send_message(ADMIN_ID, admin_text)

    photo_ids: List[str] = data.get("photo_ids", [])
    if photo_ids:
        await bot.send_message(ADMIN_ID, f"📸 Ish rasmlari: {len(photo_ids)} ta")
        # Telegram limitlarini hisobga olib birma-bir yuboramiz
        for pid in photo_ids[:10]:  # xohlasang 10 ni oshirasan
            await bot.send_photo(ADMIN_ID, pid)


async def show_summary(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (
        "📋 Ma’lumotlaringiz:\n\n"
        f"🧑‍🔧 Ism: {data.get('ism','')}\n"
        f"🛠 Yo‘nalish: {data.get('yonalish','')}\n"
        f"🧠 Tajriba: {data.get('tajriba','')}\n"
        f"🧰 Nimalar qila olasiz: {data.get('ishlar','Ko‘rsatilmagan')}\n"
        f"📍 Hudud: {data.get('hudud','')}\n"
        f"📞 Telefon: {data.get('telefon','')}\n"
        f"💬 Telegram: {data.get('telegram','')}\n\n"
        "Ma’lumotlar to‘g‘rimi?"
    )
    await state.set_state(Anketa.tasdiq)
    await message.answer(text, reply_markup=kb_confirm())


# ========= START =========
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "UstaTop Namangan botiga xush kelibsiz.\n"
        "Bot orqali anketa to‘ldirishingiz yoki reklama postingizni yuborishingiz mumkin.\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=kb_main_menu()
    )


# ========= ANKETA =========
@dp.callback_query(F.data == "anketa_start")
async def anketa_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Anketa.ism)
    await cb.message.answer("🧑‍🔧 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await cb.answer()

@dp.message(Anketa.ism)
async def anketa_ism(message: Message, state: FSMContext):
    await state.update_data(ism=message.text.strip(), photo_ids=[])
    await state.set_state(Anketa.yonalish)
    await message.answer("🛠 Yo‘nalishingizni tanlang yoki yozib yuboring:", reply_markup=kb_list(YONALISHLAR, row=1))

@dp.message(Anketa.yonalish)
async def anketa_yonalish(message: Message, state: FSMContext):
    txt = message.text.strip()
    if txt == "Boshqa (o'zim yozaman)":
        await state.set_state(Anketa.yonalish_custom)
        await message.answer("✍️ Yo‘nalishingizni yozib yuboring:", reply_markup=ReplyKeyboardRemove())
        return

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

    await state.set_state(Anketa.ishlar)
    await message.answer(
        "🧰 Bu sohada nimalar qila olasiz? (ixtiyoriy)",
        reply_markup=kb_skip_next("➡️ Keyingisi")
    )

@dp.message(Anketa.ishlar)
async def anketa_ishlar(message: Message, state: FSMContext):
    if message.text.strip() != "➡️ Keyingisi":
        await state.update_data(ishlar=message.text.strip())
    else:
        await state.update_data(ishlar="Ko‘rsatilmagan")

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
    await state.update_data(telefon=message.contact.phone_number)
    await state.set_state(Anketa.telegram)
    await message.answer("💬 Telegram username’ingizni yuboring (masalan: @username):", reply_markup=ReplyKeyboardRemove())

@dp.message(Anketa.telefon)
async def anketa_phone_text(message: Message, state: FSMContext):
    await state.update_data(telefon=message.text.strip())
    await state.set_state(Anketa.telegram)
    await message.answer("💬 Telegram username’ingizni yuboring (masalan: @username):", reply_markup=ReplyKeyboardRemove())

@dp.message(Anketa.telegram)
async def anketa_telegram(message: Message, state: FSMContext):
    await state.update_data(telegram=message.text.strip())

    # ixtiyoriy rasm bosqichi
    await state.set_state(Anketa.rasmlar)
    await message.answer(
        "📸 Ish rasmlaringiz bo‘lsa yuboring (ixtiyoriy).\n"
        "Bir nechta rasm yuborsangiz ham bo‘ladi.\n\n"
        "Tayyor bo‘lsa ➡️ O‘tkazib yuborish tugmasini bosing.",
        reply_markup=kb_skip_next("➡️ O‘tkazib yuborish")
    )

@dp.message(Anketa.rasmlar, F.photo)
async def anketa_rasmlar_add(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_ids = data.get("photo_ids", [])
    photo_ids.append(message.photo[-1].file_id)
    await state.update_data(photo_ids=photo_ids)

    await message.answer(
        f"✅ Rasm qo‘shildi. Hozircha: {len(photo_ids)} ta.\n"
        "Yana rasm yuborishingiz mumkin yoki ➡️ O‘tkazib yuborish ni bosing."
    )

@dp.message(Anketa.rasmlar)
async def anketa_rasmlar_done(message: Message, state: FSMContext):
    # Skip bosildi yoki boshqa matn yozildi
    if message.text and message.text.strip() != "➡️ O‘tkazib yuborish":
        # Matn yozsa ham rasmlarni tugatamiz (ixtiyoriy)
        pass

    await message.answer("✅ Rahmat! Endi ma’lumotlarni tekshirib ko‘ring.", reply_markup=ReplyKeyboardRemove())
    await show_summary(message, state)

@dp.callback_query(F.data == "anketa_restart")
async def anketa_restart(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Anketa.ism)
    await cb.message.answer("🔁 Qaytadan boshlaymiz.\n\n🧑‍🔧 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await cb.answer()

@dp.callback_query(F.data == "anketa_confirm")
async def anketa_confirm(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # ✅ MUHIM: bu yerda bot emas, foydalanuvchi olinadi
    user = cb.from_user

    await send_admin_anketa(user, data)

    await cb.message.answer(
        "✅ Anketangiz qabul qilindi!\n"
        "Admin ko‘rib chiqadi va tez orada kanalga joylanadi. Rahmat!",
        reply_markup=kb_main_menu()
    )
    await state.clear()
    await cb.answer()


# ========= REKLAMA POST =========
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
    # forward - media+caption ham ketadi
    await message.forward(ADMIN_ID)
    await bot.send_message(ADMIN_ID, "📌 Reklama post yuboruvchisi:\n\n" + identity_from_user(message.from_user))
    await message.answer("✅ Post adminga yuborildi. Rahmat!", reply_markup=kb_main_menu())

@dp.message()
async def fallback(message: Message):
    await message.answer("ℹ️ /start ni bosing va menyudan tanlang.", reply_markup=kb_main_menu())


# ========= RUN =========
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
