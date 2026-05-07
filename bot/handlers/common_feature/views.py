from __future__ import annotations


def build_member_help_text() -> str:
    return (
        "ℹ️ <b>Команды участника</b>\n\n"
        "🚀 <b>База</b>\n"
        "• /start — запуск бота и проверка доступа.\n"
        "• /help — показать эту подробную справку.\n"
        "• /status — быстрый признак, что бот онлайн.\n\n"
        "📅 <b>Мероприятия</b>\n"
        "• /create_event — пошагово создать мероприятие и опубликовать в группе.\n"
        "• /my_events — список ваших мероприятий и управление ими.\n"
        "• <code>/find_events &lt;текст&gt;</code> — поиск активных мероприятий по названию/описанию/месту.\n\n"
        "• <code>/set_responsible &lt;event_id&gt; &lt;user_id|@username&gt;</code> — сменить ответственного (создатель/админ).\n"
        "  Пример: <code>/set_responsible 42 @ivan</code>\n"
        "• <code>/add_participant_manual &lt;event_id&gt; &lt;user_id|@username&gt;</code> — ручное добавление.\n"
        "  Пример: <code>/add_participant_manual 42 @ivan</code>\n"
        "• <code>/send_event_card &lt;event_id&gt;</code> — отправить короткое сообщение со ссылкой на основную карточку мероприятия.\n\n"
        "📰 <b>Дайджест и подписки</b>\n"
        "• /digest — посмотреть афишу на период.\n"
        "• /subscriptions — настроить персональные уведомления.\n"
        "• /my_digest — получить персональный дайджест.\n\n"
        "📈 <b>Активность</b>\n"
        "• /my_stats — ваша статистика участий.\n"
        "• /top — топ активных участников за 30 дней.\n\n"
        "🤝 <b>Случайные встречи 1:1</b>\n"
        "• /random_optin — согласиться участвовать в случайных встречах.\n"
        "• /random_optout — отказаться от случайных встреч.\n\n"
        "💳 <b>Разделение чека</b>\n"
        "• /split_bill — пошагово создать событие разделения чека с публикацией и кнопками.\n"
        "• <code>/split_bill_add &lt;id&gt; &lt;user_id|@username&gt;</code> — добавить участника вручную (организатор).\n"
        ""
    )


def build_admin_help_text() -> str:
    return (
        "🛠 <b>Команды администратора/владельца</b>\n\n"
        "• /roles — текущая модель ролей и лимитов.\n"
        "• /usage_stats — среднее число запросов по ролям за 7 дней.\n"
        "• /debug_info — диагностическая сводка бота/группы/тем.\n"
        "• /list_topics — показать темы форума из БД.\n"
        "• /update_topic_names — синхронизировать названия тем.\n"
        "• /admin_report — управленческий отчёт по активности.\n"
        "• /send_events_list — отправить актуальный список мероприятий в выбранную группу/тему.\n"
        "• /member_reengage — отчёт по «молчащим» участникам и рекомендации, кого мягко позвать.\n"
        "• /sync_members — очистить локальный список участников от выбывших из группы.\n"
        "• /random_pairs — сформировать пары 1:1 и опубликовать их в выбранной группе/теме.\n"
        "• /pending_intro — единый отчёт по «Рассказу о себе» + кнопки отметки статуса.\n"
        "• /random_optin_count — (владелец) количество участников, согласных на 1:1.\n"
    )


def build_help_text(*, is_admin_or_owner: bool) -> str:
    member_help = build_member_help_text()
    if not is_admin_or_owner:
        return member_help
    return build_admin_help_text() + "\n" + member_help
