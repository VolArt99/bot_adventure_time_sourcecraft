from __future__ import annotations


def build_member_help_text() -> str:
    return (
        "ℹ️ <b>Команды участника</b>\n\n"
        "🚀 <b>База</b>\n"
        "• <code>/start</code> — запуск бота и проверка доступа.\n"
        "• <code>/help</code> — показать эту подробную справку.\n"
        "• <code>/status</code> — быстрый признак, что бот онлайн.\n\n"
        "📅 <b>Мероприятия</b>\n"
        "• <code>/create_event</code> — пошагово создать мероприятие и опубликовать в группе.\n"
        "• <code>/my_events</code> — список ваших мероприятий и управление ими.\n"
        "• <code>/find_events &lt;текст&gt;</code> — поиск активных мероприятий по названию/описанию/месту.\n\n"
        "• <code>/set_responsible &lt;event_id&gt; &lt;user_id|@username&gt;</code> — сменить ответственного (создатель/админ).\n"
        "  Пример: <code>/set_responsible 42 @ivan</code>\n"
        "• <code>/add_participant_manual &lt;event_id&gt; &lt;user_id|@username&gt; [иду|резерв]</code> — ручное добавление.\n"
        "  Пример: <code>/add_participant_manual 42 @ivan резерв</code>\n"
        "• <code>/send_event_card &lt;event_id&gt;</code> — переопубликовать карточку своего актуального мероприятия.\n\n"
        "📰 <b>Дайджест и подписки</b>\n"
        "• <code>/digest</code> — посмотреть афишу на период.\n"
        "• <code>/subscriptions</code> — настроить персональные уведомления.\n"
        "• <code>/my_digest</code> — получить персональный дайджест.\n\n"
        "📈 <b>Активность</b>\n"
        "• <code>/my_stats</code> — ваша статистика участий.\n"
        "• <code>/top</code> — топ активных участников за 30 дней.\n\n"
        "🤝 <b>Случайные встречи 1:1</b>\n"
        "• <code>/random_optin</code> — согласиться участвовать в случайных встречах.\n"
        "• <code>/random_optout</code> — отказаться от случайных встреч.\n\n"
        "💳 <b>Разделение чека</b>\n"
        "• <code>/split_bill</code> — пошагово создать событие разделения чека с публикацией и кнопками.\n"
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
