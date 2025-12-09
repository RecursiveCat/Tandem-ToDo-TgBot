from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from services.message_dealer import MessageDealer

create_tandem_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назвать тандем', callback_data='type_tandem_name')]
])


def generate_tracker_single_button(task_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Готово ✅', callback_data=f'task_{task_id}_single')]])


def generate_tracker_keyboard(scores=None, tasks=None):
    scores = scores or {}
    tasks = tasks or []
    
    keyboard_buttons = []

    for task in tasks:
        task_id = str(task['id'])
        title = task.get('title', f'Задача {task_id}')
        check_symbol = '✅' if scores.get(task_id) else ' '
        keyboard_buttons.append([InlineKeyboardButton(
            text=f'[{check_symbol}] {title}', 
            callback_data=f'task_{task_id}_check'
        )])

    keyboard_buttons.append([InlineKeyboardButton(text='Обновить', callback_data='check_check')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def create_pitstop_keyboard(links: List[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for link in links:
        buttons.append([InlineKeyboardButton(text=link['title'], url=link['url'])])
    
    if not buttons:
        buttons.append([InlineKeyboardButton(text="Скоро будут ссылки", url="https://example.com")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# def generate_tracker_keyboard(scores: dict):
#     #descriptions = ['Прочитали отрывок',  'Встретились', 'Выполнили задание', 'Напомнить твоему напарнику']
#     # for key, value in scores.items():
#     #     scores[key] = str(value).replace('True', '✅').replace('False', ' ')
#
#     keyboard_buttons = []
#     for category, description in zip(scores.keys(), descriptions):
#         if scores[category] is True:
#             check_symbol = '✅'
#         else:
#             check_symbol = ' '
#
#         if category != 'didnotify':
#             keyboard_buttons.append([InlineKeyboardButton(text=f'[{check_symbol}] {description}',
#                                                          callback_data=f'{category}_check')])
#         else:
#             print('ЗАШЕЛ СЮДА   ', scores['didnotify'])
#             if scores['didnotify'] is not True:
#                 keyboard_buttons.append([InlineKeyboardButton(text='Напомнить другу', callback_data='didnotify_check')])
#
#     keyboard_buttons.append([InlineKeyboardButton(text='📍 Отметить', callback_data='check_check')])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
