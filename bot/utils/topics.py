# ✅ НОВЫЙ ФАЙЛ: Утилиты для работы с темами форума

from aiogram import Bot
import logging

logger = logging.getLogger(__name__)


async def get_topics_list(bot: Bot, chat_id: int) -> list:
    """
    Безопасно получает список тем форума.
    Возвращает список словарей с ключами: message_thread_id, name
    """
    try:
        response = await bot.get_forum_topics(chat_id)

        topics = []

        # Проверяем тип ответа
        if hasattr(response, "topics"):
            # Это объект ForumTopicsInfo из aiogram
            for topic in response.topics:
                topics.append(
                    {
                        "message_thread_id": topic.message_thread_id,
                        "name": topic.name,
                        "icon_custom_emoji_id": getattr(
                            topic, "icon_custom_emoji_id", None
                        ),
                        "is_closed": getattr(topic, "is_closed", False),
                        "is_hidden": getattr(topic, "is_hidden", False),
                    }
                )
        elif isinstance(response, list):
            # Это уже список
            for topic in response:
                if isinstance(topic, dict):
                    topics.append(topic)
                else:
                    topics.append(
                        {
                            "message_thread_id": topic.message_thread_id,
                            "name": topic.name,
                        }
                    )

        logger.info(f"✅ Найдено {len(topics)} тем в группе")
        return topics

    except Exception as e:
        logger.error(f"❌ Ошибка при получении тем: {e}")
        return []


async def validate_thread_id(bot: Bot, thread_id: int, chat_id: int) -> bool:
    """
    Проверяет, существует ли тема с таким ID.
    """
    if thread_id is None:
        return True  # None озна��ает общий чат

    try:
        topics = await get_topics_list(bot, chat_id)
        return any(t["message_thread_id"] == thread_id for t in topics)
    except Exception as e:
        logger.error(f"Ошибка при проверке темы: {e}")
        return False
