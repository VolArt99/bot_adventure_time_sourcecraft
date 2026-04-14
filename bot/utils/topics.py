import logging

from database import get_all_topics, get_topic_by_id, save_forum_topic

logger = logging.getLogger(__name__)

async def get_topics_list_from_db() -> list:
    """Получает список тем из БД."""
    topics = await get_all_topics()
    logger.info("Загружено %s тем из БД", len(topics))
    return topics

async def validate_thread_id(thread_id: int | None) -> bool:
    """Проверяет существование темы в БД."""
    if thread_id in (None, 0):
        return True
    
    topic = await get_topic_by_id(thread_id)
    return topic is not None

async def update_topic_name(thread_id: int, name: str) -> bool:
    """Обновляет/добавляет тему в БД."""
    return await save_forum_topic(thread_id, name)