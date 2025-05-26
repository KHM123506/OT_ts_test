# ==== sheets/attendance.py ====
# Attendance sheet-тэй ажиллах функцүүд (checkin/checkout)
from sheets.base import get_sheet
from config import SHEET_URL_ATTENDANCE
from datetime import datetime

def is_register_number_registered(register_number):
    # Attendance-д регистр бүртгэгдсэн эсэх
    sheet = get_sheet(SHEET_URL_ATTENDANCE)
    register_numbers = sheet.col_values(3)[1:]
    return str(register_number) in register_numbers

def add_register(telegram_user_id, username, register_number, last_name, first_name):
    date = datetime.now().strftime('%Y-%m-%d')
    sheet = get_sheet(SHEET_URL_ATTENDANCE)
    row = [
        telegram_user_id,     # A
        username,             # B
        register_number,      # C
        last_name,            # D
        first_name,           # E
        'register',           # F
        date,                 # G
        '',                   # H (checkin_time)
        '',                   # I (checkout_time)
        '',                   # J (latitude)
        '',                   # K (longitude)
        '',                   # L (work_description)
        '',                   # M (photo_url)
        '',                   # N
        '',                   # O
        '',                   # P
        '',                   # Q
        '',                   # R
        '',                   # S
    ]
    sheet.append_row(row)

def add_checkin(
    telegram_user_id, 
    username, 
    register_number, 
    last_name, 
    first_name, 
    latitude, 
    longitude,
    office_name
):
    # Check-in хийх үед мэдээлэл хадгалах
    date = datetime.now().strftime('%Y-%m-%d')
    checkin_time = datetime.now().strftime('%H:%M:%S')
    sheet = get_sheet(SHEET_URL_ATTENDANCE)
    row = [
        telegram_user_id, 
        username, 
        register_number, 
        last_name, 
        first_name, 
        'checkin', 
        date, 
        checkin_time, 
        '', 
        latitude, 
        longitude, 
        '', 
        '',
        office_name
    ]
    sheet.append_row(row)

def add_checkout(
    telegram_user_id,
    username,
    register_number,
    last_name,
    first_name,
    latitude,
    longitude,
    work_description,
    photo_url,
    office_name
   ):
    date = datetime.now().strftime('%Y-%m-%d')
    checkout_time = datetime.now().strftime('%H:%M:%S')
    sheet = get_sheet(SHEET_URL_ATTENDANCE)
    row = [
        telegram_user_id,        # A
        username,                # B
        register_number,         # C
        last_name,               # D
        first_name,              # E
        'checkout',              # F
        date,                    # G
        '',                      # H (checkin_time)
        checkout_time,           # I (checkout_time)
        latitude,                # J
        longitude,               # K
        work_description,        # L
        photo_url,               # M
        office_name
    ]
    sheet.append_row(row)
