"""Клавиатуры (inline/reply) для пользовательских сценариев бота."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_keyboard(back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Клавиатура отмены с опциональным шагом назад."""
    rows: list[list[InlineKeyboardButton]] = []
    if back_callback:
        rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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


def choose_topic_keyboard(topics: list[dict], back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора темы с реальными названиями."""
    builder = InlineKeyboardBuilder()

    builder.button(text="📌 В основной чат", callback_data="topic_0")

    for topic in topics:
        topic_id = topic.get("message_thread_id") or topic.get("id")
        topic_name = topic.get("name", f"Тема {topic_id}")
        builder.button(text=f"📁 {topic_name}", callback_data=f"topic_{topic_id}")

    if back_callback:
        builder.button(text="↩️ Назад", callback_data=back_callback)
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(1)
    return builder.as_markup()


def skip_field_keyboard(field: str, back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Кнопка для пропуска опционального шага с опциональным шагом назад."""
    rows = [[InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_{field}")]]
    if back_callback:
        rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)



def event_period_mode_keyboard(back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Кнопки выбора: разовое мероприятие или период действия."""
    rows = [
        [InlineKeyboardButton(text="📍 Разовое мероприятие", callback_data="event_period_none")],
        [InlineKeyboardButton(text="📚 Период действия", callback_data="event_period_range")],
    ]
    if back_callback:
        rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def event_preview_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения мини-превью мероприятия."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Опубликовать", callback_data="event_preview_publish")],
            [InlineKeyboardButton(text="↩️ К категориям", callback_data="event_back")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")],
        ]
    )


def quick_event_templates_keyboard() -> InlineKeyboardMarkup:
    """Быстрые сценарии создания мероприятий."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📚 Книжный клуб", callback_data="template_event_book"),
                InlineKeyboardButton(text="🧠 Квиз", callback_data="template_event_quiz"),
            ],
            [
                InlineKeyboardButton(text="🎲 Настолки", callback_data="template_event_boardgames"),
                InlineKeyboardButton(text="🚶 Прогулка", callback_data="template_event_walk"),
            ],
            [InlineKeyboardButton(text="🍽 Ужин", callback_data="template_event_dinner")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu_create_event")],
        ]
    )


def main_menu_keyboard(is_admin_or_owner: bool = False) -> InlineKeyboardMarkup:
    """Визуальное меню основных команд для личных сообщений."""
    rows = [
        [
            InlineKeyboardButton(text="🎉 Создать", callback_data="menu_create_event"),
            InlineKeyboardButton(text="📅 Мои", callback_data="menu_my_events"),
        ],
        [
            InlineKeyboardButton(text="🧾 Чек", callback_data="menu_split_bill"),
            InlineKeyboardButton(text="📣 Афиша", callback_data="menu_digest"),
        ],
        [
            InlineKeyboardButton(text="🔔 Подписки", callback_data="menu_subscriptions"),
            InlineKeyboardButton(text="🤝 Комьюнити", callback_data="menu_community"),
        ],
        [InlineKeyboardButton(text="⚡ Быстрые сценарии", callback_data="menu_quick")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="menu_help")],
    ]
    if is_admin_or_owner:
        rows.append([InlineKeyboardButton(text="🛡 Админ-панель", callback_data="menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def event_price_mode_keyboard(back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Кнопки выбора модели стоимости мероприятия."""
    rows = [
        [InlineKeyboardButton(text="💰 Общая сумма", callback_data="price_mode_total")],
        [InlineKeyboardButton(text="👤 С человека", callback_data="price_mode_person")],
        [InlineKeyboardButton(text="🆓 Бесплатно", callback_data="price_mode_free")],
    ]
    if back_callback:
        rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """Кнопки выбора категории."""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=f"📂 {category.title()}", callback_data=f"category_{category}")
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def carpool_keyboard(back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Кнопки выбора карпулинга."""
    rows = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data="carpool_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="carpool_no"),
        ],
    ]
    if back_callback:
        rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_groups_keyboard(category_groups: dict[str, dict], back_callback: str | None = None) -> InlineKeyboardMarkup:
    """Клавиатура с группами категорий."""
    builder = InlineKeyboardBuilder()
    for group_key, group_data in category_groups.items():
        builder.button(
            text=str(group_data["title"]),
            callback_data=f"category_group_{group_key}",
        )
    builder.button(text="✅ Готово", callback_data="category_done")
    if back_callback:
        builder.button(text="↩️ Назад", callback_data=back_callback)    
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


def broadcast_topics_keyboard(topics: list[dict], period: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора подгруппы для публикации списка мероприятий."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 В основной чат", callback_data=f"broadcast_topic_{period}_0")

    for topic in topics:
        topic_id = topic.get("message_thread_id") or topic.get("id")
        topic_name = topic.get("name", f"Тема {topic_id}")
        builder.button(
            text=f"📁 {topic_name}",
            callback_data=f"broadcast_topic_{period}_{topic_id}",
        )

    builder.adjust(1)
    return builder.as_markup()


def random_pairs_topics_keyboard(topics: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура выбора подгруппы для публикации random 1:1 пар."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 В основной чат", callback_data="random_pairs_topic_0")

    for topic in topics:
        topic_id = topic.get("message_thread_id") or topic.get("id")
        topic_name = topic.get("name", f"Тема {topic_id}")
        builder.button(
            text=f"📁 {topic_name}",
            callback_data=f"random_pairs_topic_{topic_id}",
        )

    builder.adjust(1)
    return builder.as_markup()


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