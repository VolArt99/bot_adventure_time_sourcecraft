# Bot Adventure Time

Telegram-бот для приватного сообщества: мероприятия, участие, напоминания, дайджесты, random 1:1 встречи, онбординг новых участников и разделение чеков.

---

## Зачем нужен этот репозиторий

Проект автоматизирует рутину админов и организаторов:
- создание и публикация мероприятий в Telegram-темах (Topics);
- учёт участников (основной список + резерв);
- напоминания о событиях;
- дайджесты для группы и персональные дайджесты;
- доступ по ролям и базовый онбординг новых пользователей;
- вспомогательные сценарии вроде random-встреч 1:1 и split bill.

Если вы только открыли проект: начните с разделов **«Архитектура»**, **«Структура репозитория»**, **«Запуск»** и **«Команды»**.

---

## Технологический стек

- **Python 3.10+**
- **aiogram 3.x**
- **YDB (Yandex Database)**
- **APScheduler**
- **Yandex Cloud Functions** (webhook-режим)
- Опционально: **OpenWeatherMap** для погоды

---

## Архитектура (кратко)

### Входные точки
- **Polling/локально:** `python -m bot.main`
- **Cloud Functions/webhook:** `dynamic_handler.handler`

### Основной поток
1. Telegram update поступает в `bot.main`.
2. `Dispatcher` пропускает update через middleware/фильтры.
3. Нужный handler выполняет бизнес-логику.
4. Данные читаются/пишутся через `bot.database` → `bot.database_ydb`.
5. Для событий и уведомлений могут ставиться задания в APScheduler.

### Хранение состояния
- FSM хранится в таблице `fsm_states` (YDB), чтобы сценарии не терялись при рестартах.

---

## Структура репозитория (подробно)

```text
.
├── dynamic_handler.py
├── requirements.txt
├── промт.txt
├── README.md
├── tests/
│   ├── conftest.py
│   ├── test_access_and_flows.py
│   ├── test_database_ydb_query_patch.py
│   ├── test_database_ydb_schema_limits.py
│   ├── test_database_ydb_user_events_query.py
│   ├── test_fsm_storage_ydb.py
│   ├── test_main_init_flags.py
│   ├── test_scheduler_config.py
│   └── test_texts.py
└── bot/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── init_flags.py
    ├── constants.py
    ├── topics_config.py
    ├── texts.py
    ├── keyboards.py
    ├── check_env.py
    ├── database.py
    ├── database_ydb.py
    ├── fsm_storage_ydb.py
    ├── middleware/
    │   ├── __init__.py
    │   ├── command_access.py
    │   └── topic_discoverer.py
    ├── filters/
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── command_access.py
    │   └── registered_user.py
    ├── handlers/
    │   ├── __init__.py
    │   ├── common.py                  # фасад-совместимость
    │   ├── common_feature/            # структурный модуль common: handlers/views/services
    │   ├── events.py
    │   ├── participation.py
    │   ├── my_events.py
    │   ├── digest.py
    │   ├── subscriptions.py
    │   ├── reminders.py
    │   ├── roadmap.py
    │   ├── split_bill.py              # фасад-совместимость
    │   ├── split_bill_feature/        # структурный модуль split_bill: handlers/views/services
    │   ├── admin.py
    │   └── event_scenarios/
    │       ├── __init__.py
    │       ├── shared.py
    │       ├── create.py
    │       ├── edit.py
    │       ├── cancel.py
    │       ├── category.py
    │       └── carpool.py
    └── utils/
        ├── __init__.py
        ├── scheduler.py
        ├── weather.py
        ├── topics.py
        ├── event_links.py
        ├── helpers.py
        └── pairing.py
```

### Что где находится и за что отвечает

#### Корень проекта
- `dynamic_handler.py` — лёгкая обёртка entrypoint для Cloud Functions.
- `requirements.txt` — корневой файл зависимостей (подтягивает зависимости из `bot/requirements.txt`).
- `README.md` — этот документ.
- `промт.txt` — проектный технический промт/guide для разработки.

#### `bot/main.py`
- Инициализация бота, dispatcher, FSM storage.
- Регистрация роутеров и middleware.
- Режим polling + webhook handler.
- Ленивая инициализация БД/тем/планировщика.

#### `bot/config.py`
- Чтение env-переменных.
- Роли/лимиты/набор разрешённых команд.
- Таймзона и параметры дайджеста/напоминаний.

#### `bot/database_ydb.py`
- Создание схемы YDB таблиц.
- Все CRUD-операции по событиям, участникам, темам, random 1:1, split bill и т.д.
- Агрегации/отчёты/поисковые запросы.

#### `bot/handlers/`
- `common.py` — совместимый фасад; основная реализация в `common_feature/*`.
- `common_feature/handlers.py` — хендлеры `/start`, `/help`, `/status`, onboarding, owner approve/reject, служебные команды.
- `common_feature/services.py` — сервисные функции (проверка участия в группе, notify owner и т.д.).
- `common_feature/views.py` — формирование крупных текстов (например, `/help`).
- `events.py` + `event_scenarios/*` — FSM-сценарии создания/редактирования/категоризации событий.
- `participation.py` — inline-кнопки участия (иду/резерв/отказ, карпулинг и т.п.).
- `split_bill.py` — совместимый фасад; основная реализация в `split_bill_feature/*`.
- `split_bill_feature/handlers.py` — FSM и callback-хендлеры split bill.
- `split_bill_feature/services.py` — сервисная логика split bill (формат/обновление карточки и т.д.).
- `split_bill_feature/views.py` — текстовые шаблоны split bill.
- `roadmap.py` — статистика, top, find, random optin/optout/pairs.
- `digest.py`, `subscriptions.py`, `my_events.py`, `reminders.py` — соответствующие пользовательские функции.

#### `bot/middleware/`
- `command_access.py` — role-based доступ и лимиты команд.
- `topic_discoverer.py` — автообновление справочника тем по входящим апдейтам.

#### `bot/filters/`
- Фильтры прав (admin/registered/restricted command).

#### `bot/utils/`
- `scheduler.py` — постановка/восстановление напоминаний и периодических задач.
- `weather.py` — интеграция с погодой (с защитой от сетевых ошибок).
- `event_links.py` — карты, Google Calendar, ICS.
- `helpers.py` — mention/username/ссылки на сообщения.
- `pairing.py` — алгоритм random-пар 1:1.

#### `tests/`
- Набор unit/integration-like тестов для ключевых модулей: тексты, FSM storage, доступы, init-флаги, schema/query ограничения.

---

## Команды бота

> Фактическая доступность зависит от роли (`OWNER_ID`, `ADMIN_IDS`, approved-member) и лимитов из `config.py`.

### Базовые
- `/start` — вход/онбординг.
- `/help` — подробная справка.
- `/status` — health-lite.

### Мероприятия
- `/create_event` — пошаговое создание события.
- `/my_events` — ваши события.
- `/find_events <запрос>` — поиск по активным событиям.

### Дайджесты
- `/digest` — общий дайджест.
- `/subscriptions` — подписки.
- `/my_digest` — персональная подборка.

### Активность
- `/my_stats` — личная статистика.
- `/top` — топ участников.

### Random 1:1
- `/random_optin` — включиться в random-пулы.
- `/random_optout` — выключиться из random-пулов.
- `/random_pairs` — (admin) формирование пар.
- `/random_optin_count` — (owner) количество согласных на 1:1.

### Split bill
- `/split_bill` — пошаговый сценарий создания чека (с выбором исходного мероприятия и подгруппы публикации).
- `/split_bill_create <amount> [event_id]` — старый/быстрый формат (сохранён).
- Управление присоединением/оплатой/статусом/закрытием делается кнопками в карточке чека.
- `/split_bill_add <id> <user_id>` / `/split_bill_remove <id> <user_id>` — ручное управление участниками.

### Сервисные/админские
- `/roles`, `/usage_stats`, `/health`, `/debug_info`, `/list_topics`, `/update_topic_names`, `/admin_report`, `/pending_intro`, `/list_intro`, `/send_events_list`, `/member_reengage`.

---

## Переменные окружения

Минимально необходимые:
- `BOT_TOKEN`
- `GROUP_ID`
- `YDB_ENDPOINT`
- `YDB_DATABASE`

Обычно также нужны:
- `OWNER_ID`
- `ADMIN_IDS` (через запятую)
- `TIMEZONE` (по умолчанию `Europe/Moscow`)
- `WEATHER_API_KEY` (опционально)

Дополнительные параметры лимитов/списков команд читаются из `config.py` с безопасными default-значениями.

---

## Локальный запуск

### Установка
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Проверка окружения
```bash
python -m bot.check_env
```

### Запуск бота (polling)
```bash
python -m bot.main
```

---

## Тестирование и проверки

```bash
pytest -q
python -m compileall -q bot tests
```

Рекомендуется прогонять минимум `pytest -q` перед каждым PR.

---

## Безопасность и эксплуатационные практики

- Не храните ключи/токены в репозитории; используйте секреты CI/CD и env-переменные.
- Для YDB используйте параметризованные запросы и IAM сервисного аккаунта.
- Ограничения команд и ролей централизованы в `middleware/command_access.py` и `config.py`.
- При изменении команд/доступов синхронизируйте:
  1) `/help` тексты,  
  2) README,  
  3) `промт.txt`.

---

## Что обновилось в последних изменениях

- В карточках и списках событий явно показывается `ID` мероприятия (удобно для админских/legacy-команд).
- В `/split_bill` добавлен выбор источника участников кнопками по актуальным мероприятиям.
- В `/split_bill` добавлен выбор подгруппы (topic), куда публикуется карточка чека.
- В `/find_events` исправлено сравнение datetime (naive vs aware).

---

## CI/CD и деплой в SourceCraft + Yandex Cloud Functions

- Entry point функции: `dynamic_handler.handler`.
- Источник сборки: корень репозитория.
- ENV прокидываются через pipeline/секреты.
- Для доступа к YDB в Cloud Functions предпочтительно использовать сервисный аккаунт функции.

Полезные ссылки:
- SourceCraft CI/CD: https://sourcecraft.dev/portal/docs/ru/sourcecraft/concepts/ci-cd
- Yandex Cloud Functions: https://yandex.cloud/ru/docs/functions/
- Документация YDB: https://ydb.tech/docs/ru/?version=v25.3
- Quickstart Managed YDB: https://yandex.cloud/ru/docs/ydb/quickstart

---

## Принципы внесения изменений

1. Не ломать обратную совместимость команд без явной миграции.
2. Все SQL/YQL-запросы — параметризованные.
3. Пользовательский ввод в HTML-сообщениях — экранировать.
4. Внешние HTTP-вызовы — с timeout и exception handling.
5. Любое заметное изменение поведения — отражать в `README.md` и `промт.txt`.

---

## Частые точки диагностики

- Бот «не отвечает» в ЛС на шаге FSM:
  - проверить middleware/guard и активные состояния.
- Событие не публикуется в группу:
  - проверить `GROUP_ID`, права бота в группе/теме, наличие forum topics.
- Нет данных в БД:
  - проверить `YDB_ENDPOINT`/`YDB_DATABASE`, IAM/сервисный аккаунт.
- Нет напоминаний:
  - проверить старт scheduler и восстановление jobs.

---

##  Что обновлять при фиче

При каждом значимом изменении:
- обновить `README.md`;
- обновить `промт.txt`;
- при необходимости — добавить/обновить тесты в `tests/`;
- зафиксировать изменения в PR с описанием «что/зачем/как проверено».