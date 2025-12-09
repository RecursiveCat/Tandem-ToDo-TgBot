from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from loguru import logger

from services.database import AbstractDatabase
from handlers.admin import send_scheduled_challenges, send_scheduled_messages


async def reset_daily_stats_job(db_service: AbstractDatabase):
    try:
        await db_service.reset_daily_stats()
        logger.info("Ежедневная статистика сброшена")
    except Exception as e:
        logger.error(f"Ошибка сброса статистики: {e}")


async def send_challenges_job(bot: Bot, db_service: AbstractDatabase):
    try:
        await send_scheduled_challenges(bot, db_service)
        logger.info("Проверка запланированных челленджей выполнена")
    except Exception as e:
        logger.error(f"Ошибка отправки челленджей: {e}")


async def send_messages_job(bot: Bot, db_service: AbstractDatabase):
    try:
        await send_scheduled_messages(bot, db_service)
        logger.info("Проверка запланированных сообщений выполнена")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщений: {e}")


async def send_reminders_job(bot: Bot, db_service: AbstractDatabase):
    try:
        tasks = await db_service.get_all_tasks(active_only=True)
        if tasks:
            task_ids = [task['id'] for task in tasks]
            users_with_incomplete = await db_service.get_users_with_incomplete_tasks(task_ids)
            
            for user_data in users_with_incomplete:
                try:
                    await bot.send_message(
                        user_data['user_id'],
                        "Напоминание: у вас есть невыполненные задачи на сегодня!"
                    )
                except Exception:
                    pass
            
            logger.info(f"Напоминания отправлены {len(users_with_incomplete)} пользователям")
    except Exception as e:
        logger.error(f"Ошибка отправки напоминаний: {e}")


def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot, db_service: AbstractDatabase):
    scheduler.add_job(
        reset_daily_stats_job,
        CronTrigger(hour=0, minute=0),
        args=[db_service],
        id='reset_daily_stats',
        replace_existing=True
    )
    
    scheduler.add_job(
        send_challenges_job,
        CronTrigger(minute='*/5'),
        args=[bot, db_service],
        id='send_challenges',
        replace_existing=True
    )
    
    scheduler.add_job(
        send_messages_job,
        CronTrigger(minute='*/5'),
        args=[bot, db_service],
        id='send_messages',
        replace_existing=True
    )
    
    scheduler.add_job(
        send_reminders_job,
        CronTrigger(hour=20, minute=0),
        args=[bot, db_service],
        id='send_reminders',
        replace_existing=True
    )

