# 1. Импорт болон тохиргоо хэсэг
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from google_sheet import (
    is_telegram_id_registered, 
    add_register, 
    add_checkin, 
    add_checkout, 
    find_employee_register_row, 
    register_employee_telegram_id
    )

# 2. FSM State тодорхойлох
class RegisterStates(StatesGroup):
    waiting_for_register_number = State()
    waiting_for_confirm = State()

# 3. Ботын тохиргоо
API_TOKEN = '7352936643:AAE6VU2gzl3URACE6ik3oAbq5SgK0Itdg2g'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# 4. /register команд - шинэ бүртгэл эхлүүлэх
@dp.message_handler(commands=['register'])
async def register_handler(message: types.Message):
    user = message.from_user
    if is_telegram_id_registered(user.id):
        await message.reply("Та өмнө нь бүртгүүлсэн байна. Давхар бүртгүүлэх боломжгүй!")
        return
    await message.reply(
        "‼️ <b>Регистерийн дугаарын эхний хоёр үсгийг ТОМ үсгээр бичнэ үү!</b>\n"
        "Жишээ: <code>АА88888888</code> (AA нь том үсгээр)\n\n"
        "Өөрийн регистерийн дугаар-г оруулна уу:",
        parse_mode="HTML"
    )
    await RegisterStates.waiting_for_register_number.set()

# 5. Регистерийн дугаар шалгах, баталгаажуулах товч харуулах
@dp.message_handler(state=RegisterStates.waiting_for_register_number)
async def get_register_number(message: types.Message, state: FSMContext):
    register_number = message.text.strip()
    row_number, row = find_employee_register_row(register_number)
    if not row_number:
        await message.reply("Таны регистерийн дугаар ажилчдын жагсаалтад байхгүй байна. Админд хандана уу, эсвэл дугаараа дахин шалгаад оруулна уу:")
        return

    # Тухайн регистрийн дугаар өмнө нь бүртгэгдсэн эсэхийг шалга (employee sheet дээр telegram_user_id багана бөглөгдсөн эсэх)
    if row['telegram_user_id']:
        await message.reply("Энэ регистерийн дугаараар өмнө нь бүртгэл хийгдсэн байна!")
        return

    await state.update_data(register_number=register_number)

    # Баталгаажуулах, буцах товчтой Inline Keyboard үүсгэнэ
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Баталгаажуулах", callback_data="confirm_register"),
        InlineKeyboardButton("❌ Буцах", callback_data="back_register")
    )
    await message.reply(
        f"Таны регистерийн дугаар: {row['register_number']}\n"
        f"Овог: {row['last_name']}\n"
        f"Нэр: {row['first_name']}\n\n"
        "Таны мэдээлэл ЗӨВ бол 🟢 “Баталгаажуулах” товчийг дарна уу.\n"
        "Таны мэдэээлэл БУРУУ бол 🔴 “Буцах” товчийг дарж, регистерийн дугаараа дахин оруулна уу.",
        reply_markup=kb
    )
    await RegisterStates.waiting_for_confirm.set()

# 6. Баталгаажуулах болон буцах товчны үйлдэл
@dp.callback_query_handler(state=RegisterStates.waiting_for_confirm)
async def process_register_confirm_callback(query: types.CallbackQuery, state: FSMContext):
    if query.data == "confirm_register":
        data = await state.get_data()
        register_number = data['register_number']
        telegram_user_id = query.from_user.id
        username = query.from_user.username if query.from_user.username else ""

        # Employee sheet-ээс тухайн ажилтны мэдээллийг авах
        _, row = find_employee_register_row(register_number)
        last_name = row['last_name']
        first_name = row['first_name']

        # Attendance sheet-д бүртгэх
        add_register(
            telegram_user_id=telegram_user_id,
            username=username,
            register_number=register_number,
            last_name=last_name,
            first_name=first_name
        )

        # Employee sheet дээр мөн telegram_user_id баганад хадгалах (давхар бүртгэлээс хамгаална)
        register_employee_telegram_id(register_number, telegram_user_id)

        await query.message.edit_text(
        f"Таны бүртгэл амжилттай баталгаажлаа! ✅\n\n"
        f"Регистрийн дугаар: {register_number}\n"
        f"Овог: {last_name}\n"
        f"Нэр: {first_name}"
        )
        await state.finish()

    elif query.data == "back_register":
        await state.finish()
        await query.message.edit_text("Буцлаа. Өөрийн регистерийн дугаар-аа оруулна уу:")
        await RegisterStates.waiting_for_register_number.set()

# 7. /checkin, /checkout, байршил бүртгэх, зураг бүртгэх
@dp.message_handler(commands=['checkin'])
async def checkin_handler(message: types.Message):
    button = KeyboardButton("Байршил илгээх", request_location=True)
    markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await message.reply("Та ирсэн байрлалаа илгээнэ үү.", reply_markup=markup)

@dp.message_handler(content_types=['location'])
async def location_handler(message: types.Message):
    loc = message.location
    user = message.from_user
    add_checkin(
        telegram_user_id=user.id,
        username=user.username if user.username else "",
        register_number="",
        last_name=user.last_name if user.last_name else "",
        first_name=user.first_name if user.first_name else "",
        latitude=loc.latitude,
        longitude=loc.longitude
    )
    await message.reply("Ирсэн цаг, байршил амжилттай бүртгэгдлээ!", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(commands=['checkout'])
async def checkout_handler(message: types.Message):
    await message.reply("Ажлын тайлбараа бичээд, зураг хавсарган илгээнэ үү (зурагтай хамт тайлбар бичиж явуулна).")

@dp.message_handler(content_types=['photo'])
async def photo_handler(message: types.Message):
    user = message.from_user
    caption = message.caption if message.caption else ''
    photo_file_id = message.photo[-1].file_id if message.photo else ''
    add_checkout(
        telegram_user_id=user.id,
        username=user.username if user.username else "",
        register_number="",
        last_name=user.last_name if user.last_name else "",
        first_name=user.first_name if user.first_name else "",
        work_description=caption,
        photo_url=photo_file_id
    )
    await message.reply("Гарах цаг, ажлын тайлбар амжилттай бүртгэгдлээ!")

# 8. Ботыг ажиллуулах хэсэг (хамгийн сүүлд)
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
