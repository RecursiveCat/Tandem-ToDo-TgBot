from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Optional

def get_main_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Управление задачами', callback_data='admin_tasks')],
        [InlineKeyboardButton(text='📊 Статистика тандемов', callback_data='admin_stats')],
        [InlineKeyboardButton(text='🔗 Управление ссылками', callback_data='admin_links')],
        [InlineKeyboardButton(text='📅 Планирование челленджей', callback_data='admin_schedule')],
        [InlineKeyboardButton(text='📨 Запланированные сообщения', callback_data='admin_scheduled_messages')],
        [InlineKeyboardButton(text='📤 Рассылка сообщений', callback_data='admin_notify')],
        [InlineKeyboardButton(text='🏆 Таблица лидеров', callback_data='admin_table')],
    ])

def get_tasks_menu(tasks: List[Dict]) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        status = "✅" if task['active'] else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {task['title']}", 
                callback_data=f"task_view_{task['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text='➕ Добавить задачу', callback_data='task_add')])
    buttons.append([InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_task_detail_menu(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Редактировать', callback_data=f'task_edit_{task_id}')],
        [InlineKeyboardButton(text='🗑 Удалить', callback_data=f'task_delete_{task_id}')],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='admin_tasks')],
    ])

def get_pitstop_links_menu(links: List[Dict]) -> InlineKeyboardMarkup:
    buttons = []
    for link in links:
        status = "✅" if link['active'] else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {link['title']}", 
                callback_data=f"link_view_{link['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text='➕ Добавить ссылку', callback_data='link_add')])
    buttons.append([InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_link_detail_menu(link_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Редактировать', callback_data=f'link_edit_{link_id}')],
        [InlineKeyboardButton(text='🗑 Удалить', callback_data=f'link_delete_{link_id}')],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='admin_links')],
    ])

def get_tandems_list_menu(tandems: List[Dict]) -> InlineKeyboardMarkup:
    buttons = []
    for tandem in tandems[:20]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{tandem['name']} ({tandem['total_score']} очков)", 
                callback_data=f"tandem_stats_{tandem['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_schedule_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Создать челлендж', callback_data='schedule_challenge_add')],
        [InlineKeyboardButton(text='📋 Список запланированных', callback_data='schedule_list')],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back')],
    ])

def get_tasks_selection_menu(tasks: List[Dict], selected_ids: Optional[List[int]] = None) -> InlineKeyboardMarkup:
    selected_ids = selected_ids or []
    buttons = []
    for task in tasks:
        marker = "✅" if task['id'] in selected_ids else "☐"
        buttons.append([
            InlineKeyboardButton(
                text=f"{marker} {task['title']}", 
                callback_data=f"task_select_{task['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text='✅ Готово', callback_data='tasks_selected_done')])
    buttons.append([InlineKeyboardButton(text='◀️ Отмена', callback_data='schedule_challenge_cancel')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
