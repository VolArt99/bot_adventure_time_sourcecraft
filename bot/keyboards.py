# клавиатуры (inline-кнопки, reply-клавиатуры)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def cancel_keyboard():
    """Клавиатура отмены."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")]
    ])

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

def choose_topic_keyboard(topics):
    """Клавиатура для выбора темы."""
    builder = InlineKeyboardBuilder()
    for topic in topics:
        builder.button(text=topic.name, callback_data=f"topic_{topic.message_thread_id}")
    builder.adjust(1)
    return builder.as_markup()