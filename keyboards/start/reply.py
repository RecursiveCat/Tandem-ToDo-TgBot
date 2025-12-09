from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗺 Карта"), KeyboardButton(text="🚴‍♂️ Трекер"), KeyboardButton(text="💬 Командный чат")],
            [KeyboardButton(text="🧭 Питстоп")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите действие"
    )

