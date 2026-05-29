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
from bot.utils.design import BRAND, card_cta, card_header, card_section
from bot.utils.ui import answer_private_final


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
    paid_count = sum(1 for p in participants if p.get("is_paid"))
    waiting_count = max(0, len(participants) - paid_count)
    progress_units = 10
    filled_units = round((paid_count / len(participants)) * progress_units) if participants else 0
    progress_bar = "✅" * filled_units + "⏳" * (progress_units - filled_units)
    bank = (
        bill.get("transfer_bank_custom")
        if bill.get("transfer_bank") == "other"
        else bill.get("transfer_bank")
    ) or "—"

    lines = [
        *card_header(BRAND["money"], "Разделение чека", "Карточка сбора и статусы оплат"),
        f"🆔 ID: <code>{split_id}</code>",
        f"🧾 Название: <b>{bill.get('title') or '—'}</b>",
        f"📌 Статус: <b>{bill.get('status')}</b>",
        f"👤 Организатор: {organizer_mention}",
        f"💰 Сумма: <b>{bill.get('total_amount')} ₽</b>",
        *card_section(
            "Шкала оплат",
            [
                progress_bar,
                f"✅ оплатили: <b>{paid_count}</b> / ⏳ ждём: <b>{waiting_count}</b>",
                f"👥 участников: <b>{len(participants)}</b>",
            ],
        ),
        *card_section(
            "Реквизиты",
            [
                f"• Тип: {bill.get('transfer_target_type') or '—'}",
                f"• Куда: {bill.get('transfer_target_value') or '—'}",
                f"• Банк: {bank}",
                f"• Получатель: {bill.get('transfer_recipient_name') or '—'}",
            ],
        ),
        "",
        "<b>Участники</b>",
    ]

    if not participants:
        lines.append("—")
    else:
        for p in participants:
            uid = int(p["user_id"])
            paid = "✅" if p.get("is_paid") else "⏳"
            mention = await get_user_mention(uid, bot)
            lines.append(f"{paid} {mention} — {p.get('share_amount')} ₽")

    lines.extend(card_cta("Нажмите «Оплатил(а)», когда перевели свою долю."))
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
        title=data.get("title"),
        total_amount=amount,
        transfer_target_type=data.get("transfer_target_type"),
        transfer_target_value=data.get("transfer_target_value"),
        transfer_bank=data.get("transfer_bank"),
        transfer_bank_custom=data.get("transfer_bank_custom"),
        transfer_recipient_name=data.get("transfer_recipient_name"),
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

    await answer_private_final(
        message,
        state,
        f"✅ Чек «{data.get('title') or f'#{split_id}'}» создан и опубликован.\n"
        f"ID: {split_id}\n"
        f"Ссылка: https://t.me/c/{str(GROUP_ID).replace('-100', '')}/{sent.message_id}",
    )
    await state.clear()


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
