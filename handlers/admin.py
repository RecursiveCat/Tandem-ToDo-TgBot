from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger
from typing import Dict, List, Any, Optional
from datetime import datetime

from keyboards.admin.inline import (
    get_main_admin_menu, get_tasks_menu, get_task_detail_menu,
    get_pitstop_links_menu, get_link_detail_menu, get_tandems_list_menu,
    get_schedule_menu, get_tasks_selection_menu
)
from keyboards.start.inline import generate_tracker_single_button

from services.database import AbstractDatabase 
from services.message_dealer import MessageDealer
from states.admin import (
    Notify, TaskManagement, PitstopManagement, 
    ScheduleChallenge, ScheduleMessage
)

admin_router = Router()

@admin_router.message(F.text.startswith('/admin'))
async def on_admin_command(message: Message):
    await message.answer("Админ-панель", reply_markup=get_main_admin_menu())

@admin_router.callback_query(F.data == 'admin_back')
async def on_admin_back(call: CallbackQuery):
    await call.message.edit_text("Админ-панель", reply_markup=get_main_admin_menu())
    await call.answer()

@admin_router.callback_query(F.data == 'admin_tasks')
async def on_tasks_menu(call: CallbackQuery, db: AbstractDatabase):
    tasks = await db.get_all_tasks(active_only=False)
    await call.message.edit_text("Управление задачами", reply_markup=get_tasks_menu(tasks))
    await call.answer()

@admin_router.callback_query(F.data == 'task_add')
async def on_task_add_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите название задачи:")
    await state.set_state(TaskManagement.waiting_for_title)
    await call.answer()

@admin_router.message(TaskManagement.waiting_for_title)
async def on_task_title_received(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание задачи (или отправьте '-' для пропуска):")
    await state.set_state(TaskManagement.waiting_for_description)

@admin_router.message(TaskManagement.waiting_for_description)
async def on_task_description_received(message: Message, state: FSMContext):
    description = message.text if message.text != '-' else ''
    await state.update_data(description=description)
    await message.answer("Введите количество очков за выполнение (по умолчанию 1):")
    await state.set_state(TaskManagement.waiting_for_points)

@admin_router.message(TaskManagement.waiting_for_points)
async def on_task_points_received(message: Message, state: FSMContext, db: AbstractDatabase):
    try:
        points = int(message.text) if message.text.isdigit() else 1
    except ValueError:
        points = 1
    
    data = await state.get_data()
    task_id = await db.create_task(data['title'], data['description'], points)
    await message.answer(f"✅ Задача создана! ID: {task_id}")
    await state.clear()
    
    tasks = await db.get_all_tasks(active_only=False)
    await message.answer("Управление задачами", reply_markup=get_tasks_menu(tasks))

@admin_router.callback_query(F.data.startswith('task_view_'))
async def on_task_view(call: CallbackQuery, db: AbstractDatabase):
    task_id = int(call.data.split('_')[-1])
    task = await db.get_task(task_id)
    if not task:
        await call.answer("Задача не найдена", show_alert=True)
        return
    
    status = "Активна" if task['active'] else "Неактивна"
    text = f"Задача #{task['id']}\n\n"
    text += f"Название: {task['title']}\n"
    text += f"Описание: {task.get('description', 'Нет описания')}\n"
    text += f"Очки: {task['points']}\n"
    text += f"Статус: {status}"
    
    await call.message.edit_text(text, reply_markup=get_task_detail_menu(task_id))
    await call.answer()

@admin_router.callback_query(F.data.startswith('task_delete_'))
async def on_task_delete(call: CallbackQuery, db: AbstractDatabase):
    task_id = int(call.data.split('_')[-1])
    await db.delete_task(task_id)
    await call.answer("Задача удалена")
    
    tasks = await db.get_all_tasks(active_only=False)
    await call.message.edit_text("Управление задачами", reply_markup=get_tasks_menu(tasks))

@admin_router.callback_query(F.data.startswith('task_edit_'))
async def on_task_edit(call: CallbackQuery, db: AbstractDatabase, state: FSMContext):
    task_id = int(call.data.split('_')[-1])
    task = await db.get_task(task_id)
    if not task:
        await call.answer("Задача не найдена", show_alert=True)
        return
    
    await state.update_data(task_id=task_id)
    await call.message.answer(
        f"Редактирование задачи: {task['title']}\n\n"
        "Отправьте новое название (или '-' для пропуска), затем описание, затем очки, затем 'active' или 'inactive' для статуса"
    )
    await state.set_state(TaskManagement.waiting_for_edit_field)
    await call.answer()

@admin_router.message(TaskManagement.waiting_for_edit_field)
async def on_task_edit_received(message: Message, state: FSMContext, db: AbstractDatabase):
    data = await state.get_data()
    task_id = data.get('task_id')
    if not task_id:
        await message.answer("Ошибка: не найден ID задачи")
        await state.clear()
        return
    
    parts = message.text.split('\n', 2)
    title = parts[0] if len(parts) > 0 and parts[0] != '-' else None
    description = parts[1] if len(parts) > 1 and parts[1] != '-' else None
    points_str = parts[2] if len(parts) > 2 else None
    points = int(points_str) if points_str and points_str.isdigit() else None
    
    await db.update_task(task_id, title=title, description=description, points=points)
    await message.answer("✅ Задача обновлена")
    await state.clear()
    
    tasks = await db.get_all_tasks(active_only=False)
    await message.answer("Управление задачами", reply_markup=get_tasks_menu(tasks))

@admin_router.callback_query(F.data == 'admin_links')
async def on_links_menu(call: CallbackQuery, db: AbstractDatabase):
    links = await db.get_pitstop_links(active_only=False)
    await call.message.edit_text("Управление ссылками Питстоп", reply_markup=get_pitstop_links_menu(links))
    await call.answer()

@admin_router.callback_query(F.data == 'link_add')
async def on_link_add_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите название ссылки:")
    await state.set_state(PitstopManagement.waiting_for_title)
    await call.answer()

@admin_router.message(PitstopManagement.waiting_for_title)
async def on_link_title_received(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите URL ссылки:")
    await state.set_state(PitstopManagement.waiting_for_url)

@admin_router.message(PitstopManagement.waiting_for_url)
async def on_link_url_received(message: Message, state: FSMContext, db: AbstractDatabase):
    url = message.text
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    data = await state.get_data()
    link_id = await db.add_pitstop_link(data['title'], url)
    await message.answer(f"✅ Ссылка добавлена! ID: {link_id}")
    await state.clear()
    
    links = await db.get_pitstop_links(active_only=False)
    await message.answer("Управление ссылками Питстоп", reply_markup=get_pitstop_links_menu(links))

@admin_router.callback_query(F.data.startswith('link_view_'))
async def on_link_view(call: CallbackQuery, db: AbstractDatabase):
    link_id = int(call.data.split('_')[-1])
    links = await db.get_pitstop_links(active_only=False)
    link = next((l for l in links if l['id'] == link_id), None)
    if not link:
        await call.answer("Ссылка не найдена", show_alert=True)
        return
    
    text = f"Ссылка #{link_id}\n\nНазвание: {link['title']}\nURL: {link['url']}"
    await call.message.edit_text(text, reply_markup=get_link_detail_menu(link_id))
    await call.answer()

@admin_router.callback_query(F.data.startswith('link_delete_'))
async def on_link_delete(call: CallbackQuery, db: AbstractDatabase):
    link_id = int(call.data.split('_')[-1])
    await db.delete_pitstop_link(link_id)
    await call.answer("Ссылка удалена")
    
    links = await db.get_pitstop_links(active_only=False)
    await call.message.edit_text("Управление ссылками Питстоп", reply_markup=get_pitstop_links_menu(links))

@admin_router.callback_query(F.data == 'admin_stats')
async def on_stats_menu(call: CallbackQuery, db: AbstractDatabase):
    tandems = await db.get_all_tandems_with_summary()
    await call.message.edit_text("Выберите тандем для просмотра статистики:", reply_markup=get_tandems_list_menu(tandems))
    await call.answer()

@admin_router.callback_query(F.data.startswith('tandem_stats_'))
async def on_tandem_stats(call: CallbackQuery, db: AbstractDatabase):
    tandem_id = int(call.data.split('_')[-1])
    stats = await db.get_tandem_statistics(tandem_id, days=7)
    summary = await db.get_tandem_summary(tandem_id)
    
    text = f"Статистика тандема #{tandem_id}\n\n"
    text += f"Участники: {', '.join(summary.get('user_names', []))}\n"
    text += f"Общий счет: {stats['total_score']} очков\n"
    text += f"Выполнено задач за 7 дней: {stats['tasks_completed']}\n"
    text += f"Выполнения по дням: {len(stats['completions_by_day'])} дней"
    
    await call.message.edit_text(text, reply_markup=get_main_admin_menu())
    await call.answer()

@admin_router.callback_query(F.data == 'admin_schedule')
async def on_schedule_menu(call: CallbackQuery):
    await call.message.edit_text("Планирование челленджей", reply_markup=get_schedule_menu())
    await call.answer()

@admin_router.callback_query(F.data == 'schedule_challenge_add')
async def on_schedule_challenge_add(call: CallbackQuery, state: FSMContext, db: AbstractDatabase):
    tasks = await db.get_all_tasks(active_only=True)
    if not tasks:
        await call.answer("Нет активных задач. Сначала создайте задачи.", show_alert=True)
        return
    
    await state.update_data(selected_task_ids=[])
    await call.message.edit_text("Выберите задачи для челленджа:", reply_markup=get_tasks_selection_menu(tasks, []))
    await call.answer()

@admin_router.callback_query(F.data.startswith('task_select_'))
async def on_task_select(call: CallbackQuery, state: FSMContext, db: AbstractDatabase):
    task_id = int(call.data.split('_')[-1])
    data = await state.get_data()
    selected_ids = data.get('selected_task_ids', [])
    
    if task_id in selected_ids:
        selected_ids.remove(task_id)
    else:
        selected_ids.append(task_id)
    
    await state.update_data(selected_task_ids=selected_ids)
    tasks = await db.get_all_tasks(active_only=True)
    await call.message.edit_reply_markup(reply_markup=get_tasks_selection_menu(tasks, selected_ids))
    await call.answer()

@admin_router.callback_query(F.data == 'tasks_selected_done')
async def on_tasks_selected_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_ids = data.get('selected_task_ids', [])
    if not selected_ids:
        await call.answer("Выберите хотя бы одну задачу", show_alert=True)
        return
    
    await call.message.answer("Введите текст сообщения для челленджа (или '-' для пропуска):")
    await state.set_state(ScheduleChallenge.waiting_for_message_text)
    await call.answer()

@admin_router.message(ScheduleChallenge.waiting_for_message_text)
async def on_challenge_message_received(message: Message, state: FSMContext):
    message_text = message.text if message.text != '-' else None
    await state.update_data(message_text=message_text)
    await message.answer(
        "Введите время отправки в формате:\n"
        "YYYY-MM-DD HH:MM (например: 2024-12-25 10:00)\n"
        "Или отправьте 'now' для немедленной отправки"
    )
    await state.set_state(ScheduleChallenge.waiting_for_send_time)

@admin_router.message(ScheduleChallenge.waiting_for_send_time)
async def on_challenge_send_time_received(message: Message, state: FSMContext, db: AbstractDatabase, bot: Bot):
    data = await state.get_data()
    selected_ids = data.get('selected_task_ids', [])
    message_text = data.get('message_text')
    
    if message.text.lower() == 'now':
        send_time = datetime.now()
    else:
        try:
            send_time = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        except ValueError:
            await message.answer("Неверный формат времени. Используйте: YYYY-MM-DD HH:MM")
            return
    
    challenge_id = await db.create_scheduled_challenge(selected_ids, send_time, message_text)
    await message.answer(f"✅ Челлендж запланирован! ID: {challenge_id}")
    
    if send_time <= datetime.now():
        await message.answer("⏰ Время уже наступило, отправляю челлендж...")
        await send_scheduled_challenges(bot, db)
    
    await state.clear()

@admin_router.callback_query(F.data == 'admin_notify')
async def on_notify_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Отправьте сообщение для рассылки (текст или переслать сообщение):")
    await state.set_state(Notify.wait_for_content)
    await call.answer()

@admin_router.message(Notify.wait_for_content)
async def on_notify_content_received(message: Message, state: FSMContext, bot: Bot, db: AbstractDatabase):
    if message.text == '/stop':
        await message.answer("Рассылка отменена")
        await state.clear()
        return
    
    users = await db.get_all_users()
    sent = 0
    failed = 0
    
    for user_id in users:
        try:
            if hasattr(message, 'forward_from_message_id') and message.forward_from_message_id:
                await bot.forward_message(user_id, message.chat.id, message.forward_from_message_id)
            elif message.text:
                await bot.send_message(user_id, message.text)
            else:
                await bot.copy_message(user_id, message.chat.id, message.message_id)
            sent += 1
        except TelegramForbiddenError:
            failed += 1
        except Exception as e:
            logger.error(f"Ошибка отправки {user_id}: {e}")
            failed += 1
    
    await message.answer(f"Рассылка завершена. Отправлено: {sent}, Ошибок: {failed}")
    await state.clear()

@admin_router.callback_query(F.data == 'admin_scheduled_messages')
async def on_scheduled_messages_menu(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Отправьте сообщение для планирования (текст или переслать):")
    await state.set_state(ScheduleMessage.waiting_for_message)
    await call.answer()

@admin_router.message(ScheduleMessage.waiting_for_message)
async def on_scheduled_message_received(message: Message, state: FSMContext):
    if message.text == '/stop':
        await message.answer("Планирование отменено")
        await state.clear()
        return
    
    await state.update_data(message_data={
        'text': message.text,
        'forward_from_message_id': getattr(message, 'forward_from_message_id', None),
        'target_chat_id': message.chat.id
    })
    await message.answer(
        "Введите время отправки в формате:\n"
        "YYYY-MM-DD HH:MM (например: 2024-12-25 10:00)\n"
        "Или отправьте 'now' для немедленной отправки"
    )
    await state.set_state(ScheduleMessage.waiting_for_send_time)

@admin_router.message(ScheduleMessage.waiting_for_send_time)
async def on_scheduled_message_time_received(message: Message, state: FSMContext, db: AbstractDatabase, bot: Bot):
    data = await state.get_data()
    msg_data = data.get('message_data', {})
    
    if message.text.lower() == 'now':
        send_time = datetime.now()
    else:
        try:
            send_time = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        except ValueError:
            await message.answer("Неверный формат времени. Используйте: YYYY-MM-DD HH:MM")
            return
    
    message_id = await db.create_scheduled_message(
        message_type='broadcast',
        scheduled_time=send_time,
        target_chat_id=msg_data.get('target_chat_id'),
        forward_from_message_id=msg_data.get('forward_from_message_id'),
        text=msg_data.get('text')
    )
    
    await message.answer(f"✅ Сообщение запланировано! ID: {message_id}")
    
    if send_time <= datetime.now():
        await message.answer("⏰ Время уже наступило, отправляю сообщение...")
        await send_scheduled_messages(bot, db)
    
    await state.clear()

@admin_router.callback_query(F.data == 'admin_table')
async def on_table_receive(call: CallbackQuery, db: AbstractDatabase, md: MessageDealer):
    tandems = await db.get_all_tandems_with_summary()
    
    if not tandems:
        await call.message.answer("Нет тандемов")
        await call.answer()
        return
    
    message_lines = [md.get_ui('leaderboard_title')]
    
    for i, tandem in enumerate(tandems[:50]):
        users_in_tandem = ", ".join(tandem.get('user_names', []) or [])
        line = md.get_ui('leaderboard_line') % {
            'rank': i + 1,
            'name': tandem['name'],
            'id': tandem['id'],
            'score': tandem['total_score'],
            'users': users_in_tandem
        }
        message_lines.append(line)
    
    await call.message.answer("\n".join(message_lines))
    await call.answer()

@admin_router.callback_query(F.data.startswith('task_') & F.data.endswith('_single'))
async def on_task_complete_from_challenge(call: CallbackQuery, db: AbstractDatabase):
    task_id_str = call.data.replace('_single', '').replace('task_', '')
    try:
        task_id = int(task_id_str)
    except ValueError:
        await call.answer("Ошибка: неверный ID задачи")
        return
    
    new_status = await db.toggle_task(call.from_user.id, task_id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer(f'✅ Отмечено выполнение задачи')
    logger.info(f'{call.from_user.id} отметил выполнение задачи {task_id} (статус: {new_status})')

async def send_scheduled_challenges(bot: Bot, db: AbstractDatabase):
    challenges = await db.get_pending_scheduled_challenges()
    tasks = await db.get_all_tasks(active_only=True)
    task_dict = {task['id']: task for task in tasks}
    users = await db.get_all_users()
    
    for challenge in challenges:
        task_ids = challenge['task_ids']
        message_text = challenge.get('message_text', '')
        
        for user_id in users:
            try:
                if message_text:
                    await bot.send_message(user_id, message_text)
                
                for task_id in task_ids:
                    if task_id in task_dict:
                        task = task_dict[task_id]
                        keyboard = generate_tracker_single_button(task_id)
                        await bot.send_message(
                            user_id,
                            f"<b>{task['title']}</b>\n{task.get('description', '')}",
                            reply_markup=keyboard
                        )
            except TelegramForbiddenError:
                pass
            except Exception as e:
                logger.error(f"Ошибка отправки челленджа {user_id}: {e}")
        
        await db.mark_challenge_sent(challenge['id'])

async def send_scheduled_messages(bot: Bot, db: AbstractDatabase):
    messages = await db.get_pending_scheduled_messages()
    users = await db.get_all_users()
    
    for msg in messages:
        for user_id in users:
            try:
                if msg['forward_from_message_id'] and msg['target_chat_id']:
                    await bot.forward_message(
                        user_id,
                        msg['target_chat_id'],
                        msg['forward_from_message_id']
                    )
                elif msg['text']:
                    await bot.send_message(user_id, msg['text'])
            except TelegramForbiddenError:
                pass
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения {user_id}: {e}")
        
        await db.mark_message_sent(msg['id'])

@admin_router.message(F.text == '/test_reset')
async def on_test_reset(message: Message, db: AbstractDatabase):
    await db.reset_daily_stats()
    await message.answer("✅ Статистика сброшена (тест)")

@admin_router.message(F.text == '/test_challenges')
async def on_test_challenges(message: Message, bot: Bot, db: AbstractDatabase):
    await send_scheduled_challenges(bot, db)
    await message.answer("✅ Челленджи отправлены (тест)")

@admin_router.message(F.text == '/test_messages')
async def on_test_messages(message: Message, bot: Bot, db: AbstractDatabase):
    await send_scheduled_messages(bot, db)
    await message.answer("✅ Сообщения отправлены (тест)")

@admin_router.message(F.text == '/test_reminders')
async def on_test_reminders(message: Message, bot: Bot, db: AbstractDatabase):
    tasks = await db.get_all_tasks(active_only=True)
    if not tasks:
        await message.answer("Нет активных задач")
        return
    
    task_ids = [task['id'] for task in tasks]
    users_with_incomplete = await db.get_users_with_incomplete_tasks(task_ids)
    
    for user_data in users_with_incomplete:
        try:
            await bot.send_message(
                user_data['user_id'],
                "Напоминание: у вас есть невыполненные задачи на сегодня!"
            )
        except TelegramForbiddenError:
            pass
    
    await message.answer(f"✅ Напоминания отправлены {len(users_with_incomplete)} пользователям (тест)")
