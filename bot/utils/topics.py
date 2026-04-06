# ✅ ИСПРАВЛЕННЫЙ ФАЙЛ: bot/utils/topics.py

from database import get_all_topics, get_topic_by_id, save_forum_topic
import logging

logger = logging.getLogger(__name__)

async def get_topics_list_from_db() -> list:
    """
    Получает список тем из базы данных.
    Темы обнаруживаются автоматически через middleware.
    """
    topics = await get_all_topics()
    logger.info(f"✅ Загружено {len(topics)} тем из БД")
    return topics

async def validate_thread_id(thread_id: int) -> bool:
    """
    Проверяет, существует ли тема с таким ID в БД.
    """
    if thread_id is None:
        return True  # None означает общий чат
    
    topic = await get_topic_by_id(thread_id)
    is_valid = topic is not None
    logger.info(f"✅ Проверка thread_id {thread_id}: {is_valid}")
    return is_valid

async def update_topic_name(thread_id: int, name: str) -> bool:
    """
    Обновляет название темы в БД.
    """
    return await save_forum_topic(thread_id, name)