# Telegram ID болон регистртэй холбоотой логикууд
from sheets.employees import find_employee_register_row, register_employee_telegram_id
from sheets.attendance import is_register_number_registered
from sheets.base import get_sheet
from config import SHEET_URL_EMPLOYEES, SHEET_URL_ATTENDANCE

def is_telegram_id_registered(telegram_user_id):
    # Telegram ID өмнө нь бүртгэгдсэн эсэхийг шалгах
    sheet_emp = get_sheet(SHEET_URL_EMPLOYEES)
    emp_users = sheet_emp.col_values(4)[1:]
    if str(telegram_user_id) in emp_users:
        return True

    sheet_att = get_sheet(SHEET_URL_ATTENDANCE)
    att_users = sheet_att.col_values(1)[1:]
    return str(telegram_user_id) in att_users

# Цагийн бүртгэлийн Sheet-рүү Регистерийн дугаар татах
def get_register_number_by_telegram_id(telegram_id):
    sheet = get_sheet(SHEET_URL_EMPLOYEES)
    rows = sheet.get_all_values()
    for row in rows[1:]:  # гарчигыг алгасана
        if str(row[3]) == str(telegram_id):  # 4-р багана telegram_user_id гэж үзье
            return row[0]  # 1-р багана нь register number гэж үзэж байна
    return ""
