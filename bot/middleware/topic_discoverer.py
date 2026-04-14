import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

logger = logging.getLogger(__name__)

class TopicDiscovererMiddleware(BaseMiddleware):
    """
    Middleware, который автоматически обнаруживает темы форума
    и использует названия из конфига или БД.
    """
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем тип события
        if hasattr(event, "message") and event.message is not None:
            message = event.message

            # Проверяем, есть ли в сообщении информация о теме
            if hasattr(message, "message_thread_id") and message.message_thread_id:
                message_thread_id = message.message_thread_id

                # Получаем название темы из конфига или генерируем
                topic_name = self._get_topic_name(message_thread_id)

                from bot.database import save_forum_topic

                try:
                    await save_forum_topic(message_thread_id, topic_name)
                    logger.info(
                        "topic_discovered user_id=%s command=%s event_id=%s thread_id=%s topic_name=%s",
                        getattr(getattr(message, "from_user", None), "id", None),
                        (message.text or "").split(" ", 1)[0] if message.text else None,
                        getattr(message, "message_id", None),
                        message_thread_id,
                        topic_name,
                    )
                except (TypeError, ValueError) as exc:
                    logger.warning(
                        "topic_discover_failed user_id=%s event_id=%s thread_id=%s error=%s",
                        getattr(getattr(message, "from_user", None), "id", None),
                        getattr(message, "message_id", None),
                        message_thread_id,
                        type(exc).__name__,
                    )
        
        return await handler(event, data)
    
    def _get_topic_name(self, thread_id: int) -> str:
        """
        Получает название темы из конфига.
        """
        try:
            from bot.topics_config import TOPICS_MAPPING
            
            if thread_id in TOPICS_MAPPING:
                name = TOPICS_MAPPING[thread_id]
                logger.info(f"Используется название из конфига: {name}")
                return name
            else:
                logger.warning(f"ID темы {thread_id} не в конфиге, используется ID как название")
                return f"Тема {thread_id}"
        except ImportError:
            logger.warning("topics_config.py не найден, используется ID как название")
            return f"Тема {thread_id}"
        except (TypeError, ValueError):
            logger.warning("Некорректный thread_id=%s, используется fallback-название", thread_id)
            return f"Тема {thread_id}"