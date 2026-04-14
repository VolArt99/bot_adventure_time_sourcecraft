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
    builder.button(text="🗑 Удалить мероприятие", callback_data=f"delete_{event_id}")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ choose_topic_keyboard() в keyboards.py


def choose_topic_keyboard(topics):
    """Клавиатура для выбора темы с реальными названиями."""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопку "В основной чат"
    builder.button(text="📌 В основной чат", callback_data="topic_0")

    # Добавляем все темы с их реальными названиями
    for topic in topics:
        topic_id = topic.get("message_thread_id") or topic.get("id")
        # ✅ НОВОЕ: Используем реальное название темы
        topic_name = topic.get("name", f"Тема {topic_id}")
        builder.button(text=f"📁 {topic_name}", callback_data=f"topic_{topic_id}")

    builder.adjust(1)
    return builder.as_markup()


# ⚠️ НОВОЕ: Клавиатура для моих мероприятий

def skip_field_keyboard(field: str) -> InlineKeyboardMarkup:
    """Кнопка для пропуска опционального шага."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_{field}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")],
        ]
    )


def category_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """Кнопки выбора категории."""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=f"📂 {category.title()}", callback_data=f"category_{category}")
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def carpool_keyboard() -> InlineKeyboardMarkup:
    """Кнопки выбора карпулинга."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="carpool_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="carpool_no"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")],
        ]
    )


def category_groups_keyboard(category_groups: dict[str, dict]) -> InlineKeyboardMarkup:
    """Клавиатура с группами категорий."""
    builder = InlineKeyboardBuilder()
    for group_key, group_data in category_groups.items():
        builder.button(
            text=str(group_data["title"]),
            callback_data=f"category_group_{group_key}",
        )
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(1)
    return builder.as_markup()


def category_subgroups_keyboard(
    group_key: str,
    category_groups: dict[str, dict],
    selected_categories: list[str],
) -> InlineKeyboardMarkup:
    """Клавиатура выбора подкатегорий (множественный выбор)."""
    builder = InlineKeyboardBuilder()
    group = category_groups[group_key]
    subcategories = group["subcategories"]

    for category in subcategories:
        marker = "✅ " if category in selected_categories else ""
        builder.button(
            text=f"{marker}{category.title()}",
            callback_data=f"category_toggle_{category}",
        )

    builder.button(text="↩️ К группам", callback_data="category_back")
    builder.button(text="✅ Готово", callback_data="category_done")
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def my_events_keyboard(events: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком мероприятий пользователя."""
    builder = InlineKeyboardBuilder()
    for event in events[:10]:  # Максимум 10
        builder.button(
            text=f"📅 {event['title'][:20]}", callback_data=f"myevent_{event['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


def period_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура выбора периода."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📆 За неделю", callback_data=f"{prefix}_week")
    builder.button(text="🗓 За месяц", callback_data=f"{prefix}_month")
    builder.button(text="🧾 За всё время", callback_data=f"{prefix}_all")
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


def onboarding_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Старт", callback_data="onboarding_start")]
        ]
    )


def rules_ack_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Правила изучил(а) ❤️", callback_data="rules_ack")]
        ]
    )


def owner_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять в группу", callback_data=f"approve_user_{user_id}"),
                InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_user_{user_id}"),
            ]
        ]
    )


def intro_status_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выполнено", callback_data=f"intro_done_{user_id}"),
                InlineKeyboardButton(text="✏️ Изменить статус", callback_data=f"intro_toggle_{user_id}"),
            ]
        ]
    )