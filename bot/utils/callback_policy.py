"""Единая политика завершения callback-хендлеров.

Правило удаления сообщений бота:
- CALLBACK_DELETE_WIZARD_MESSAGE=True — шаговые меню в ЛС/FSM wizard flows,
  где старое меню должно исчезнуть после выбора.
- CALLBACK_KEEP_PUBLIC_MESSAGE=False — публичные group callbacks и карточки,
  где сообщение должно оставаться и обновляться/редактироваться.
"""

CALLBACK_DELETE_WIZARD_MESSAGE = True
CALLBACK_KEEP_PUBLIC_MESSAGE = False
