# ==== mybot/handlers/user.py ====
# Хэрэглэгчийн command, FSM registration, checkin/checkout болон зураг хадгалах
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# mybot/handlers/user.py
from mybot.main import dp

from mybot import dp
from services.registration import is_telegram_id_registered, get_register_number_by_telegram_id
from sheets.employees import find_employee_register_row, register_employee_telegram_id
from sheets.attendance import add_register, add_checkin, add_checkout
from utils.geo import find_nearest_office
from config import SHEET_URL_LOCATION, CREDS_FILE, WORKSHEET_NAME
from sheets.base import get_offices_from_sheet

# FSM-ийн үе шатууд
class RegisterStates(StatesGroup):
    waiting_for_register_number = State()
    waiting_for_confirm = State()

class CheckoutStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_photo = State()
    waiting_for_description = State()
    
# /register command ашиглан бүртгэл эхлүүлэх
@dp.message_handler(commands=['register'])
async def register_handler(message: types.Message):
    user = message.from_user
    if is_telegram_id_registered(user.id):
        await message.reply("Та өмнө нь бүртгүүлсэн байна.")
        return
    await message.reply(
        "‼️ <b>Регистерийн дугаарын эхний хоёр үсгийг ТОМ үсгээр бичнэ үү!</b>\n"
        "Жишээ: <code>АА88888888</code> (AA нь том үсгээр)\n\n"
        "Өөрийн регистерийн дугаар-г оруулна уу:",
        parse_mode="HTML"
    )
    await RegisterStates.waiting_for_register_number.set()

# Регистр шалгах, баталгаажуулах товч харагдуулах
@dp.message_handler(state=RegisterStates.waiting_for_register_number)
async def get_register_number(message: types.Message, state: FSMContext):
    register_number = message.text.strip()
    row_number, row = find_employee_register_row(register_number)
    if not row_number:
        await message.reply("Бүртгэл олдсонгүй.")
        return
    if row['telegram_user_id']:
        await message.reply("Энэ регистер бүртгэгдсэн байна.")
        return
    await state.update_data(register_number=register_number)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Баталгаажуулах", callback_data="confirm_register"),
        InlineKeyboardButton("❌ Буцах", callback_data="back_register")
    )
    await message.reply(f"Овог: {row['last_name']}\nНэр: {row['first_name']}", reply_markup=kb)
    await RegisterStates.waiting_for_confirm.set()

# Баталгаажуулах товчны callback
@dp.callback_query_handler(state=RegisterStates.waiting_for_confirm)
async def process_register_confirm_callback(query: types.CallbackQuery, state: FSMContext):
    if query.data == "confirm_register":
        data = await state.get_data()
        register_number = data['register_number']
        telegram_user_id = query.from_user.id
        username = query.from_user.username or ""
        _, row = find_employee_register_row(register_number)
        add_register(telegram_user_id, username, register_number, row['last_name'], row['first_name'])
        register_employee_telegram_id(register_number, telegram_user_id)
        await query.message.edit_text("Бүртгэл амжилттай.")
        await state.finish()
    elif query.data == "back_register":
        await state.finish()
        await query.message.edit_text("Регистерийн дугаараа дахин оруулна уу.")
        await RegisterStates.waiting_for_register_number.set()

# /checkin команд, байршил авах
@dp.message_handler(commands=['checkin'])
async def checkin_handler(message: types.Message):
    await message.reply(
        "🚩 Байршлаа илгээнэ үү!\n\n"
        "❗️ Зөвхөн \"Live Location\" (хөдөлгөөнт байршил) илгээнэ.\n\n"
        "Доорх дарааллаар илгээнэ үү:\n"
        "1. 📎 (Attach) дээр дарна\n"
        "2. Location → Share live location for ... гэж сонгоно"
    )

  # Байршил хүлээж авах үед checkin хийх
@dp.message_handler(content_types=['location'])
async def location_handler(message: types.Message):
    loc = message.location
    # Заавал live_location шалгана
    if not loc.live_period:
        await message.reply(
            "‼️ Та заавал 'Live Location' (хөдөлгөөнт байршил) илгээнэ үү!\n\n"
            "Доорх дарааллаар илгээнэ үү:\n"
            "1. 📎 (Attach) дээр дарна\n"
            "2. Location → Share live location for ... гэж сонгоно"
    )
        return
    user = message.from_user
    register_number = get_register_number_by_telegram_id(user.id)

    offices = get_offices_from_sheet(SHEET_URL_LOCATION, CREDS_FILE, WORKSHEET_NAME)
    is_inside, office_name, distance = find_nearest_office(loc.latitude, loc.longitude, offices)

    if not is_inside:
        await message.reply("Та зөвшөөрөгдсөн радиус дотор байхгүй байна.")
        return

    add_checkin(
        user.id, 
        user.username or "", 
        register_number,
        user.last_name or "", 
        user.first_name or "",
        loc.latitude, 
        loc.longitude,
        office_name
    )
    await message.reply(f"Checkin бүртгэгдлээ. Байршил: {office_name}, Зай: {int(distance)}м", reply_markup=ReplyKeyboardRemove())

# 1. /checkout команд – эхлээд зураг илгээхийг асууна
@dp.message_handler(commands=['checkout'])
async def checkout_handler(message: types.Message):
    await message.reply(
        "🚩 Байршлаа илгээнэ үү!\n\n"
        "❗️ Зөвхөн \"Live Location\" (хөдөлгөөнт байршил) илгээнэ.\n\n"
        "Доорх дарааллаар илгээнэ үү:\n"
        "1. 📎 (Attach) дээр дарна\n"
        "2. Location → Share live location for ... гэж сонгоно"
    )
    await CheckoutStates.waiting_for_location.set()

# Байршил хүлээж авах үед ажлын зураг асууна.
@dp.message_handler(content_types=['location'], state=CheckoutStates.waiting_for_location)
async def process_checkout_location(message: types.Message, state: FSMContext):
    loc = message.location
    offices = get_offices_from_sheet(SHEET_URL_LOCATION, CREDS_FILE, WORKSHEET_NAME)
    is_inside, office_name, distance = find_nearest_office(loc.latitude, loc.longitude, offices)

    if not is_inside:
        await message.reply("Та зөвшөөрөгдсөн радиус дотор байхгүй байна.")
        return
    if not loc.live_period:
        await message.reply(
            "‼️ Та заавал 'Live Location' (хөдөлгөөнт байршил) илгээнэ үү!\n\n"
            "Доорх дарааллаар илгээнэ үү:\n"
            "1. 📎 (Attach) дээр дарна\n"
            "2. Location → Share live location for ... гэж сонгоно"
    )
        return

    await state.update_data(latitude=loc.latitude, longitude=loc.longitude)
    await state.update_data(office_name=office_name)
    await message.reply("Одоо ажлын зургийг илгээнэ үү:", reply_markup=ReplyKeyboardRemove())
    await CheckoutStates.waiting_for_photo.set()

# Ажлын зураг хүлээж авах үед ажлын тайлбар асууна.
@dp.message_handler(content_types=['photo'], state=CheckoutStates.waiting_for_photo)
async def process_checkout_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_ids = data.get('photo_file_ids', [])  # өмнө цугларсан зураг байвал авна
    photo_ids.append(message.photo[-1].file_id)  # шинэ зураг бүрийг list-д нэмнэ
    await state.update_data(photo_file_ids=photo_ids)  # list-ийг state-д хадгална
    await message.reply("Ажлын тайлбарыг бичнэ үү:")
    await CheckoutStates.waiting_for_description.set()

@dp.message_handler(state=CheckoutStates.waiting_for_photo)
async def photo_required_warning(message: types.Message, state: FSMContext):
    await message.reply("‼️ Заавал зураг илгээнэ үү! 📷")


# Ажлын тайлбар хүлээж авах үед Checkout хийнэ.
@dp.message_handler(state=CheckoutStates.waiting_for_description)
async def process_checkout_description(message: types.Message, state: FSMContext):
    user = message.from_user   # Энэ мөрийг хамгийн эхэнд нэмэх ёстой!
    description = message.text
    data = await state.get_data()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    register_number = get_register_number_by_telegram_id(user.id)
    office_name = data.get("office_name")
    photo_file_ids = data.get('photo_file_ids', [])
    photo_ids_str = ','.join(photo_file_ids)

    add_checkout(
        user.id,
        user.username or "",
        register_number,
        user.last_name or "",
        user.first_name or "",
        latitude,
        longitude,
        description,
        photo_ids_str,
        office_name
    )
    await message.reply("Checkout бүртгэгдлээ!", reply_markup=ReplyKeyboardRemove())
    await state.finish()



@dp.message_handler(lambda msg: msg.text in [
    "📝 Шинээр бүртгүүлэх",
    "✅ Ажил ЭХЭЛСЭН цаг бүртгүүлэх",
    "🏁 Ажил ДУУССАН цаг бүртгүүлэх"
])
async def menu_text_router(message: types.Message):
    if message.text == "📝 Шинээр бүртгүүлэх":
        await register_handler(message)
    elif message.text == "✅ Ажил ЭХЭЛСЭН цаг бүртгүүлэх":
        await checkin_handler(message)
    elif message.text == "🏁 Ажил ДУУССАН цаг бүртгүүлэх":
        await checkout_handler(message)

