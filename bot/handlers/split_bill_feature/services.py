from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import GROUP_ID
from bot.database import (
    add_split_bill_participant,
    close_split_bill,
    create_split_bill,
    get_event_participant_ids,
    get_split_bill,
    get_split_bill_participants,
    mark_split_bill_paid,
    remove_split_bill_participant,
)
from bot.utils.helpers import get_user_mention


def parse_args(message: Message) -> list[str]:
    return (message.text or "").split()[1:]


def split_bill_actions(split_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Присоединиться", callback_data=f"sb_join_{split_id}"),
                InlineKeyboardButton(text="🚪 Выйти", callback_data=f"sb_leave_{split_id}"),
            ],
            [
                InlineKeyboardButton(text="💸 Оплатил(а)", callback_data=f"sb_paid_{split_id}"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"sb_status_{split_id}"),
            ],
            [InlineKeyboardButton(text="🔒 Закрыть чек", callback_data=f"sb_close_{split_id}")],
        ]
    )


async def format_split_bill_text(split_id: int, bot) -> str:
    bill = await get_split_bill(split_id)
    if not bill:
        return "❌ Событие разделения чека не найдено."

    participants = await get_split_bill_participants(split_id)
    organizer_mention = await get_user_mention(int(bill["organizer_id"]), bot)
    lines = [
        f"💳 <b>Разделение чека #{split_id}</b>",
        f"Статус: <b>{bill.get('status')}</b>",
        f"Организатор: {organizer_mention}",
        f"Сумма: <b>{bill.get('total_amount')} ₽</b>",
        f"Участников: <b>{len(participants)}</b>",
        "",
        "<b>Участники:</b>",
    ]

    if not participants:
        lines.append("—")
    else:
        for p in participants:
            uid = int(p["user_id"])
            paid = "✅" if p.get("is_paid") else "⌛"
            mention = await get_user_mention(uid, bot)
            lines.append(f"{paid} {mention} — {p.get('share_amount')} ₽")

    return "\n".join(lines)


async def finalize_split_bill(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    amount = float(data["total_amount"])
    source_event_id = data.get("source_event_id")
    creator_id = int(data["creator_id"])
    thread_id = data.get("thread_id")

    split_id = await create_split_bill(
        group_id=GROUP_ID,
        organizer_id=creator_id,
        total_amount=amount,
        source_event_id=source_event_id,
    )

    initial_participants: list[int] = []
    if source_event_id:
        initial_participants = await get_event_participant_ids(source_event_id)

    if creator_id not in initial_participants:
        initial_participants.append(creator_id)

    for uid in sorted(set(initial_participants)):
        await add_split_bill_participant(split_id, uid)

    text = await format_split_bill_text(split_id, message.bot)
    sent = await message.bot.send_message(
        GROUP_ID,
        text,
        message_thread_id=thread_id,
        parse_mode="HTML",
        reply_markup=split_bill_actions(split_id),
    )

    await state.clear()
    await message.answer(
        f"✅ Чек «{data.get('title') or f'#{split_id}'}» создан и опубликован.\n"
        f"ID: {split_id}\n"
        f"Ссылка: https://t.me/c/{str(GROUP_ID).replace('-100', '')}/{sent.message_id}"
    )


async def refresh_split_message(callback: CallbackQuery, split_id: int) -> None:
    bill = await get_split_bill(split_id)
    if not bill:
        return
    text = await format_split_bill_text(split_id, callback.bot)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=split_bill_actions(split_id))
    except Exception:
        pass


async def close_bill_if_ready(split_id: int) -> bool:
    participants = await get_split_bill_participants(split_id)
    if not participants or any(not bool(p.get("is_paid")) for p in participants):
        return False
    await close_split_bill(split_id)
    return True


__all__ = [
    "add_split_bill_participant",
    "close_bill_if_ready",
    "finalize_split_bill",
    "format_split_bill_text",
    "get_split_bill",
    "get_split_bill_participants",
    "mark_split_bill_paid",
    "parse_args",
    "refresh_split_message",
    "remove_split_bill_participant",
    "split_bill_actions",
]
