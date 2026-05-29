from __future__ import annotations

from bot.utils.design import BRAND, card_cta, card_header, card_section


def build_main_menu_text(*, is_admin_or_owner: bool) -> str:
    """Стильный текст главного меню в ЛС."""
    lines = [
        *card_header("✨", "Adventure Time Control Center", "Единая панель действий бота"),
        *card_section(
            "Разделы",
            [
                f"{BRAND['event']} <b>События</b> — создать встречу, афишу, быстрый шаблон.",
                f"{BRAND['money']} <b>Деньги</b> — разделить чек и отметить оплаты.",
                f"{BRAND['notify']} <b>Уведомления</b> — подписки и персональные дайджесты.",
                f"{BRAND['community']} <b>Комьюнити</b> — random 1:1 и активность.",
            ],
        ),
        *card_cta("Выберите действие кнопкой ниже."),
    ]
    if is_admin_or_owner:
        lines.insert(-2, f"{BRAND['admin']} <i>Вам доступен админ-раздел.</i>")
    return "\n".join(lines)


def build_menu_section_text(section: str, *, is_admin_or_owner: bool) -> str | None:
    """Возвращает красивую карточку раздела главного меню."""
    sections = {
        "create_event": (
            [
                *card_header(BRAND["event"], "Создание мероприятия", "Мастер карточки события"),
                *card_section(
                    "Что заполнит мастер",
                    [
                        "• название, описание, дату старта и период действия;",
                        "• место, стоимость, лимит, карпулинг и тему публикации;",
                        "• перед публикацией покажет мини-превью карточки.",
                    ],
                ),
                *card_cta("Команда: /create_event или быстрый шаблон ниже."),
            ]
        ),
        "my_events": (
            [
                *card_header(BRAND["calendar"], "Мои мероприятия", "Управление созданными событиями"),
                *card_section("Возможности", ["• посмотреть свои события;", "• отправить ссылку на карточку;", "• назначить ответственного или добавить участника."]),
                *card_cta("Команда: /my_events"),
            ]
        ),
        "split_bill": (
            [
                *card_header(BRAND["money"], "Разделение чека", "Карточка сбора и статусы оплат"),
                *card_section("Что будет в карточке", ["• сумма и доля на участника;", "• реквизиты и получатель;", "• визуальная шкала: ✅ оплатили / ⏳ ждём."]),
                *card_cta("Команда: /split_bill"),
            ]
        ),
        "digest": (
            [
                *card_header("📣", "Афиша и поиск", "Быстрый доступ к событиям"),
                *card_section("Команды", ["• /digest — общая афиша;", "• /my_digest — персональная подборка;", "• <code>/find_events &lt;текст&gt;</code> — поиск."]),
                *card_cta("Выберите афишу или используйте поиск."),
            ]
        ),
        "subscriptions": (
            [
                *card_header(BRAND["notify"], "Подписки и уведомления", "Только релевантные события"),
                *card_section("Настройки", ["• категории интересов;", "• персональный дайджест;", "• режим уведомлений."]),
                *card_cta("Команды: /subscriptions, /my_digest"),
            ]
        ),
        "community": (
            [
                *card_header(BRAND["community"], "Комьюнити и активность", "Знакомства и статистика"),
                *card_section("Команды", ["• /random_optin и /random_optout — random 1:1;", "• /my_stats — личная статистика;", "• /top — топ активности."]),
                *card_cta("Включайтесь в комьюнити-активности."),
            ]
        ),
        "help": (
            [
                *card_header(BRAND["help"], "Помощь", "Справка по командам"),
                *card_section("Где искать", ["• /help — полная справка по ролям и сценариям;", "• /menu — вернуться в Control Center."]),
                *card_cta("Если не знаете, с чего начать — нажмите /menu."),
            ]
        ),
        "quick": (
            [
                *card_header(BRAND["event"], "Быстрые сценарии", "Шаблоны для мастера мероприятия"),
                *card_section("Доступные шаблоны", ["📚 Книжный клуб", "🧠 Квиз", "🎲 Настолки", "🚶 Прогулка", "🍽 Ужин" ]),
                *card_cta("Нажмите шаблон — бот подставит название, описание и категорию."),
            ]
        ),
    }
    if section == "admin":
        if not is_admin_or_owner:
            return None
        return "\n".join([
            *card_header(BRAND["admin"], "Админ-панель", "Диагностика, отчёты и управление"),
            *card_section("Инструменты", ["• /admin_report и /usage_stats — отчёты;", "• /send_events_list — публикация списка;", "• /pending_intro — контроль рассказа о себе;", "• /list_topics и /debug_info — диагностика."]),
            *card_cta("Используйте аккуратно: команды доступны по ролям."),
        ])
    section_lines = sections.get(section)
    return "\n".join(section_lines) if section_lines else None


def build_member_help_text() -> str:
    return (
        "ℹ️ <b>Команды участника</b>\n\n"
        "🚀 <b>База</b>\n"
        "• /start — запуск бота и проверка доступа.\n"
        "• /help — показать эту подробную справку.\n"
        "• /menu — открыть стильное кнопочное меню.\n"
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
