from aiogram import Router, F, Bot
from aiogram.utils.deep_linking import create_start_link
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger
from typing import List, Dict

from keyboards.start.reply import get_main_menu
from keyboards.start.inline import create_tandem_button, generate_tracker_keyboard, create_pitstop_keyboard
from services.database import AbstractDatabase
from services.message_dealer import MessageDealer
from states import ChooseName

start_router = Router()


@start_router.message(CommandStart())
async def on_command_start(message: Message, bot: Bot, db: AbstractDatabase, state: FSMContext, md: MessageDealer):
    logger.info(f'{message.from_user.id} нажал /start')
    user_id = message.from_user.id

    if message.text.startswith('/start ref'):
        refer_user_id_str = message.text.split('ref')[-1]
        
        if not refer_user_id_str.isdigit():
             return await message.answer(md.get_error("invalid_referral_id"))

        refer_user_id = int(refer_user_id_str)

        if refer_user_id == user_id:
            return await message.answer(md.get_error('self_referral'))
        
        partner_info = await db.get_tandem_info(refer_user_id)
        if partner_info:
            return await message.answer(md.get_error("tandem_is_complete")) 
        
        if not await db.get_tandem_info(user_id): 
            await db.create_tandem(user_id, refer_user_id)
            await message.answer(md.get_registration_message('reg_notification_1'))
            await bot.send_message(refer_user_id, md.get_registration_message('reg_notification_2'),
                                   reply_markup=create_tandem_button) 
            logger.info(f'{user_id} создал тандем с {refer_user_id}')

    user_info = await db.get_user_info(user_id)
    if user_info and user_info.get('name') == 'Безымянный пользователь': 
        await message.answer(md.get_registration_message('write_your_name'))
        await state.set_state(ChooseName.personal_name)
        logger.info(f'{user_id} перешел в стейт ChooseName.personal_name')
        return

    if not await db.get_tandem_info(user_id):
        refer_link = await create_start_link(bot, 'ref' + str(user_id))
        await message.answer(md.get_registration_message('share_with_friends') % refer_link)
        logger.info(f'{user_id} получил реф ссылку')
    else:
        await message.answer(md.get_functional_message('start'), reply_markup=get_main_menu())


@start_router.callback_query(F.data == 'type_tandem_name')
async def on_type_tandem_name(call: CallbackQuery, db: AbstractDatabase, state: FSMContext, md: MessageDealer):
    tandem_info = await db.get_tandem_info(call.from_user.id)
    if not tandem_info:
        await call.answer(md.get_error('no_tandem'), show_alert=True)
        return
    await call.message.answer(md.get_registration_message('write_tandem_name'))
    await state.set_state(ChooseName.tandem_name)


@start_router.message(ChooseName.personal_name)
async def on_personal_name_recieved(message: Message, db: AbstractDatabase, state: FSMContext, bot: Bot, md: MessageDealer):
    user_id = message.from_user.id
    name = message.text.strip()
    
    if not (1 < len(name) < 20):
        return await message.answer(md.get_error_message("incorrect_name"))
        
    await db.set_name(user_id, name)
    await message.answer(md.get_registration_message("you_are_registered") % name)

    if not await db.get_tandem_info(user_id):
        refer_link = await create_start_link(bot, 'ref' + str(user_id))
        await message.answer(md.get_registration_message('share_with_friends') % refer_link)
        logger.info(f'{user_id} получил реф ссылку')
        
    await state.clear()


@start_router.message(ChooseName.tandem_name)
async def on_tandem_name_recieved(message: Message, db: AbstractDatabase, state: FSMContext, bot: Bot, md: MessageDealer):
    user_id = message.from_user.id
    tandem_name = message.text.strip()
    
    if not (1 < len(tandem_name) < 20):
        return await message.answer(md.get_error_message("incorrect_name"))
    
    tandem_info = await db.get_tandem_info(user_id)
    if not tandem_info:
        await state.clear()
        return await message.answer(md.get_error("no_tandem"))

    await db.set_tandem_name(tandem_info['tandem_id'], tandem_name)
    
    partner_id = await db.get_partner_id(user_id)

    registration_message = md.get_registration_message("tandem_registered") \
                             % (tandem_info['partner_name'], tandem_name)

    for uid in [partner_id, user_id]:
        await bot.send_message(uid, registration_message, reply_markup=get_main_menu())
        await bot.send_message(uid, md.get_functional_message('tandem_start_info')) 
    
    await state.clear()


@start_router.message(F.text == '🚴‍♂️ Трекер')
async def on_text_tracker(message: Message, db: AbstractDatabase, md: MessageDealer):
    tracker_data: Dict[str, bool] = await db.get_today_stats(message.from_user.id) 
    tasks = await db.get_all_tasks(active_only=True)

    await message.answer(md.get_functional_message('tracker'),
                         reply_markup=generate_tracker_keyboard(tracker_data, tasks))
    logger.info(f'{message.from_user.id} Нажал на трекер')

@start_router.callback_query(F.data.startswith('task_') & F.data.endswith('_check'))
async def on_tracker_check(call: CallbackQuery, bot: Bot, db: AbstractDatabase, md: MessageDealer):
    user_id = call.from_user.id
    data = call.data
    
    if data == 'check_check':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        return

    task_id_str = data.replace('_check', '').replace('task_', '')
    try:
        task_id = int(task_id_str)
    except ValueError:
        await call.answer("Ошибка: неверный ID задачи")
        return

    await db.toggle_task(user_id, task_id)
    
    tracker_data = await db.get_today_stats(user_id)
    tasks = await db.get_all_tasks(active_only=True)
    
    await bot.edit_message_text(md.get_functional_message('tracker'),
                     chat_id=call.message.chat.id, message_id=call.message.message_id,
                     reply_markup=generate_tracker_keyboard(tracker_data, tasks))
    await call.answer()


@start_router.message(F.text == '🗺 Карта')
async def on_text_map(message: Message, db: AbstractDatabase, md: MessageDealer):
    user_id = message.from_user.id
    tandem_info = await db.get_tandem_info(user_id)
    
    if not tandem_info:
        return await message.answer(md.get_error('not_in_tandem_map'))

    tandem_id = tandem_info['tandem_id']
    partner_id = tandem_info['partner_id']
    
    summary = await db.get_tandem_score_breakdown(tandem_id) 

    if not summary:
        return await message.answer(md.get_error('no_data'))

    user_values = summary.get(user_id, 0)
    partner_values = summary.get(partner_id, 0)
    total_score = user_values + partner_values

    logger.info(f'{user_id} Нажал на карту. Тандем: {tandem_id}, Scores: {summary}')

    caption = md.get_map_message(
        day=1, 
        user_name1=tandem_info['partner_name'],
        score1=partner_values,
        user_name2=tandem_info['name'],
        score2=user_values,
        total_score=total_score
    )

    await message.answer(f"Карта для тандема {tandem_id}:\n" + caption)


@start_router.message(F.text == '🧭 Питстоп')
async def on_text_pitstop(message: Message, db: AbstractDatabase, md: MessageDealer):
    links = await db.get_pitstop_links()
    kb = create_pitstop_keyboard(links)
    await message.answer(md.get_functional_message('pitstop_menu'), reply_markup=kb)


@start_router.message(F.text == '💬 Командный чат')
async def on_team_chat(message: Message, md: MessageDealer):
    await message.answer(md.get_functional_message('team_chat'))


@start_router.callback_query(F.data =='delete_me')
async def on_delete_button_clicked(call: CallbackQuery, db: AbstractDatabase, bot: Bot, md: MessageDealer):
    user_id = call.from_user.id
    
    tandem_info = await db.get_tandem_info(user_id)
    if not tandem_info:
        return await bot.answer_callback_query(call.id, md.get_error('not_in_tandem'))

    partner_id = tandem_info['partner_id']
    
    await db.disband_tandem(user_id) 
    
    refer_link = await create_start_link(bot, 'ref' + str(user_id))
    await bot.edit_message_text(md.get_functional_message('disband_self') % refer_link, 
                                chat_id=user_id, message_id=call.message.message_id)

    await bot.send_message(partner_id, md.get_functional_message('disband_partner') % refer_link)

    logger.info(f"{user_id} вышел, тандем {tandem_info['tandem_name']} расформирован")
