# Bot Adventure Time

Telegram-бот для управления мероприятиями в приватной группе с включёнными форум-темами (Telegram Topics).

## Что уже реализовано

- Создание, редактирование и отмена мероприятий через сценарии (`/create_event`, `/edit_event`, `/cancel_event`).
- Публикация анонсов в выбранные темы и динамическое обновление карточки мероприятия.
- Управление участием: основной список, резерв, подтверждения, карпулинг.
- Напоминания до события с восстановлением задач после перезапуска.
- Дайджесты: общий (`/digest`) и персональный (`/my_digest`) по подпискам.
- Дополнительные команды сообщества: `/my_events`, `/my_stats`, `/top`, `/find_events`, random-пары.
- Ограничение команд через middleware и фильтры доступа.

---

## Структура репозитория

```text
.
├── dynamic_handler.py               # Entrypoint для Yandex Cloud Functions
├── requirements.txt                 # Зависимости для Cloud Functions (-r bot/requirements.txt)
├── bot/
│   ├── main.py                      # Логика инициализации + async handler/update processing
│   ├── config.py                    # Переменные окружения и лимиты
│   ├── database.py                  # Адаптер импорта БД (package/script режим)
│   ├── database_ydb.py              # Работа с YDB: схемы, CRUD, отчёты, статистика
│   ├── constants.py                 # Константы домена (категории, статусы и т.д.)
│   ├── texts.py                     # Форматирование сообщений, дайджестов и напоминаний
│   ├── keyboards.py                 # Inline/reply-клавиатуры
│   ├── topics_config.py             # Первичная конфигурация форум-тем
│   ├── check_env.py                 # Утилита диагностики окружения
│   ├── handlers/
│   │   ├── common.py                # /start, /help, /health, служебные команды
│   │   ├── events.py                # Публичные обработчики карточек события
│   │   ├── participation.py         # Кнопки участия и логика переходов
│   │   ├── reminders.py             # Ручные операции с напоминаниями
│   │   ├── digest.py                # /digest
│   │   ├── my_events.py             # /my_events
│   │   ├── subscriptions.py         # Подписки и /my_digest
│   │   ├── roadmap.py               # /my_stats, /top, /find_events, random-функции
│   │   ├── admin.py                 # Админ-отчёты
│   │   └── event_scenarios/         # FSM-сценарии create/edit/cancel/category/carpool
│   ├── middleware/
│   │   ├── command_access.py        # Ограничение доступа к командам
│   │   └── topic_discoverer.py      # Автообновление тем при апдейтах
│   ├── filters/
│   │   ├── admin.py                 # Проверка администраторов
│   │   ├── registered_user.py       # Проверка пользователя
│   │   └── command_access.py        # Фильтры команд
│   └── utils/
│       ├── scheduler.py             # APScheduler: старт/восстановление job'ов
│       ├── weather.py               # OpenWeatherMap с защитой от таймаутов
│       ├── topics.py                # Работа с темами из БД
│       ├── helpers.py               # Юзернеймы, упоминания, ссылки на сообщения
│       ├── event_links.py           # Ссылки карты/Google Calendar/ICS
│       └── pairing.py               # Алгоритм формирования random-пар 1:1
├── tests/
│   ├── test_texts.py                # Базовые unit-тесты форматтеров и ссылок
│   ├── test_access_and_flows.py     # Проверки прав доступа + onboarding/approve/reject
│   └── test_scheduler_config.py     # Проверки scheduler (parse_mode + digest config)
├── README.md
└── промт.txt                        # Актуальный продуктово-технический промт
```

---

## Команды

### Пользовательские

- `/start` — старт и онбординг.
- `/help` — справка по командам.
- `/status` — быстрый статус бота (доступен до одобрения).
- `/create_event` — создание мероприятия.
- `/edit_event` — редактирование мероприятия.
- `/cancel_event` — отмена мероприятия.
- `/my_events` — мои мероприятия.
- `/digest` — общий дайджест.
- `/subscriptions` — подписки по категориям.
- `/my_digest` — персональный дайджест.
- `/my_stats` — личная статистика.
- `/top` — топ участников.
- `/find_events` — поиск активных событий.
- `/random_optin`, `/random_optout` — участие в random-встречах.

### Админские/служебные

- `/admin_report`
- `/debug_info`
- `/list_topics`
- `/update_topic_names`
- `/pending_intro`
- `/list_intro`
- `/random_pairs`
- `/health`
- `/status`

---

## Безопасность и устойчивость

- Команды ограничены middleware/фильтрами по роли и членству в группе.
- Взаимодействие с БД идёт через параметризованные запросы YDB.
- Права владельца унифицированы через `OWNER_ID` (без смешения с chat-id).
- Для не одобренных пользователей явно whitelist-ятся `/start`, `/help`, `/status` (остальные команды блокируются до аппрува).
- Telegram Bot API не даёт надёжного «листинга всех тем» одной командой: бот сохраняет темы по входящим сообщениям + `topics_config.py`.
- Формирование пользовательских текстов в карточках мероприятия экранируется (`html.escape`).
- Интеграция с погодой защищена от сетевых ошибок и таймаутов.
- Инициализация бота защищена lock-механизмом от повторного запуска при гонках.
- FSM хранится в YDB (таблица `fsm_states`), поэтому состояния пользователей сохраняются между рестартами без Redis.
- Параметры подключения к YDB (`YDB_ENDPOINT`, `YDB_DATABASE`) должны быть заданы явно.


## Проверки

```bash
pytest -q
python -m compileall -q bot tests
python -m bot.main
```

## CI/CD для Cloud Functions

- В SourceCraft workflow использует `YC_FUNCTION_ENTRYPOINT=dynamic_handler.handler` и `SOURCE_PATH="."`, чтобы в рантайме был доступен пакет `bot` с абсолютными импортами (`from bot...`).
- Переменные окружения функции передаются через `ENVIRONMENT` в `.sourcecraft/ci.yaml`: `BOT_TOKEN`, `WEATHER_API_KEY`, `GROUP_ID`, `ADMIN_IDS`, `OWNER_ID`, `YDB_ENDPOINT`, `YDB_DATABASE`, `TIMEZONE`.
- Для установки зависимостей на стороне функции используется корневой `requirements.txt`, который подключает `bot/requirements.txt`.
- Для доступа к YDB в Cloud Functions нужно явно задать креды (например, `YDB_SERVICE_ACCOUNT_KEY_CONTENT_CREDENTIALS` c JSON-ключом сервисного аккаунта или `YDB_SERVICE_ACCOUNT_KEY_FILE_CREDENTIALS`). Авто-fallback на metadata endpoint в функциях часто недоступен и приводит к таймаутам.