# клавиатуры (inline-кнопки, reply-клавиатуры)

# ⚠️ ОБНОВЛЕНО: Добавлены новые клавиатуры

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")]
        ]
    )


def event_actions(event_id: int, carpool_enabled: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для мероприятия."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Пойду", callback_data=f"join_{event_id}")
    builder.button(text="❌ Отказаться", callback_data=f"decline_{event_id}")
    builder.button(text="⏳ В резерв", callback_data=f"waitlist_{event_id}")
    if carpool_enabled:
        builder.button(text="🚗 Еду на машине", callback_data=f"driver_{event_id}")
        builder.button(text="👥 Ищу попутку", callback_data=f"passenger_{event_id}")
    builder.adjust(2, 2)
    return builder.as_markup()


# ✅ ИЗМЕНЕНИЕ: Функция choose_topic_keyboard() - исправляем работу с объектами ForumTopic


def choose_topic_keyboard(topics):
    """Клавиатура для выбора темы (исправленная версия)."""
    builder = InlineKeyboardBuilder()
    for topic in topics:
        # topics может быть список dict'ов или ForumTopic объектов
        # Извлекаем данные правильно
        if isinstance(topic, dict):
            # Если это словарь (из API)
            topic_id = topic.get("message_thread_id")
            topic_name = topic.get("name", f"Тема {topic_id}")
        else:
            # Если это объект ForumTopic из aiogram
            topic_id = topic.message_thread_id
            topic_name = topic.name

        builder.button(text=topic_name, callback_data=f"topic_{topic_id}")
    builder.adjust(1)
    return builder.as_markup()


# ⚠️ НОВОЕ: Клавиатура для моих мероприятий
def my_events_keyboard(events: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком мероприятий пользователя."""
    builder = InlineKeyboardBuilder()
    for event in events[:10]:  # Максимум 10
        builder.button(
            text=f"📅 {event['title'][:20]}", callback_data=f"myevent_{event['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


# ⚠️ НОВОЕ: Клавиатура настроек уведомлений
def notification_settings_keyboard(current: str) -> InlineKeyboardMarkup:
    """Клавиатура настроек уведомлений."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Все уведомления", callback_data="notify_all")
    builder.button(text="📍 Только мои", callback_data="notify_mine")
    builder.button(text="🔕 Отключить", callback_data="notify_off")
    if current == "all":
        builder.button(text="✅ Текущее: Все", callback_data="notify_current")
    elif current == "mine":
        builder.button(text="✅ Текущее: Только мои", callback_data="notify_current")
    else:
        builder.button(text="✅ Текущее: Отключено", callback_data="notify_current")
    builder.adjust(1)
    return builder.as_markup()
