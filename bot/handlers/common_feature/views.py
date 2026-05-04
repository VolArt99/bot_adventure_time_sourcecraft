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
        "• <code>/add_participant_manual &lt;event_id&gt; &lt;user_id|@username&gt; [иду|резерв]</code> — ручное добавление.\n"
        "  Пример: <code>/add_participant_manual 42 @ivan резерв</code>\n"
        "• <code>/send_event_card &lt;event_id&gt;</code> — переопубликовать карточку своего актуального мероприятия.\n\n"
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
        "• <code>/roles</code> — текущая модель ролей и лимитов.\n"
        "• <code>/usage_stats</code> — среднее число запросов по ролям за 7 дней.\n"
        "• <code>/debug_info</code> — диагностическая сводка бота/группы/тем.\n"
        "• <code>/health</code> — быстрый health-check.\n"
        "• <code>/list_topics</code> — показать темы форума из БД.\n"
        "• <code>/update_topic_names</code> — синхронизировать названия тем.\n"
        "• <code>/admin_report</code> — управленческий отчёт по активности.\n"
        "• <code>/send_events_list</code> — отправить актуальный список мероприятий в выбранную группу/тему.\n"
        "• <code>/member_reengage</code> — отчёт по «молчащим» участникам и рекомендации, кого мягко позвать.\n"
        "• <code>/sync_members</code> — очистить локальный список участников от выбывших из группы.\n"
        "• <code>/random_pairs</code> — сформировать пары 1:1 среди согласившихся.\n"
        "• <code>/pending_intro</code> — единый отчёт по «Рассказу о себе» + кнопки отметки статуса.\n"
        "• <code>/random_optin_count</code> — (владелец) количество участников, согласных на 1:1.\n"
    )


def build_help_text(*, is_admin_or_owner: bool) -> str:
    member_help = build_member_help_text()
    if not is_admin_or_owner:
        return member_help
    return build_admin_help_text() + "\n" + member_help
