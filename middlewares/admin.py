from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        router = data.get('router')
        if router and router.name != 'admin':
            return await handler(event, data)
        
        config = data.get('config')
        if not config:
            return await handler(event, data)
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if user_id and user_id not in config.bot.admin_ids:
            if isinstance(event, CallbackQuery):
                await event.answer("У вас нет прав администратора", show_alert=True)
            elif isinstance(event, Message) and event.text and event.text.startswith('/admin'):
                await event.answer("У вас нет прав администратора")
            return
        
        return await handler(event, data)

