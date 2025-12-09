import asyncio
import sys
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from handlers import all_routers
from services import PostgresService, MessageDealer
from services.scheduler import setup_scheduler
from middlewares import AdminMiddleware
from handlers.admin import admin_router

def setup_logging():
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>")
    logger.add("logs/bot.log", rotation="5 MB", compression="zip", level="DEBUG")

async def main():
    setup_logging()

    config = load_config()

    db_service = PostgresService(dsn=config.db.dsn)
    md = MessageDealer()

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    admin_middleware = AdminMiddleware()
    admin_router.message.middleware(admin_middleware)
    admin_router.callback_query.middleware(admin_middleware)

    for router in all_routers:
        dp.include_router(router)

    scheduler = AsyncIOScheduler()

    @dp.startup()
    async def on_startup():
        await db_service.connect()
        await db_service.create_default_tables()
        setup_scheduler(scheduler, bot, db_service)
        scheduler.start()
        logger.info("Планировщик задач запущен")
        logger.info("Бот запущен успешно")

    @dp.shutdown()
    async def on_shutdown():
        scheduler.shutdown()
        logger.info("Планировщик задач остановлен")
        logger.info("Бот остановлен")

    await dp.start_polling(
        bot,
        db_service=db_service,
        config=config,
        md=md
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот прервал свою работу системным вызовом")
