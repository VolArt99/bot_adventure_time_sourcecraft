from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import GROUP_ID
from bot.database import (
    add_split_bill_participant,
    close_split_bill,
    create_split_bill,
    get_event_participant_ids,
    get_split_bill,
    get_split_bill_participants,
    is_member_approved,
    mark_split_bill_paid,
    remove_split_bill_participant,
)

router = Router(name=__name__)


def _parse_args(message: Message) -> list[str]:
    return (message.text or "").split()[1:]


@router.message(Command("split_bill_create"))
async def cmd_split_bill_create(message: Message):
    args = _parse_args(message)
    if not args:
        await message.answer(
            "💳 Использование: /split_bill_create <сумма> [event_id]\\n"
            "Пример: /split_bill_create 4200 15"
        )
        return

    try:
        amount = float(args[0])
    except ValueError:
        await message.answer("❌ Сумма должна быть числом.")
        return

    source_event_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    split_id = await create_split_bill(
        group_id=GROUP_ID,
        organizer_id=message.from_user.id,
        total_amount=amount,
        source_event_id=source_event_id,
    )

    initial_participants: list[int] = []
    if source_event_id:
        initial_participants = await get_event_participant_ids(source_event_id)

    if message.from_user.id not in initial_participants:
        initial_participants.append(message.from_user.id)

    for uid in sorted(set(initial_participants)):
        await add_split_bill_participant(split_id, uid)

    await message.answer(
        f"✅ Создано событие разделения чека #{split_id}.\\n"
        f"Участников: {len(set(initial_participants))}.\\n"
        f"Дальше используйте: /split_bill_status {split_id}"
    )


@router.message(Command("split_bill_join"))
async def cmd_split_bill_join(message: Message):
    args = _parse_args(message)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /split_bill_join <split_id>")
        return

    if not await is_member_approved(message.from_user.id):
        await message.answer("❌ Присоединиться может только участник группы.")
        return

    split_id = int(args[0])
    bill = await get_split_bill(split_id)
    if not bill:
        await message.answer("❌ Событие не найдено.")
        return
    if bill.get("status") != "open":
        await message.answer("⛔ Событие уже закрыто.")
        return

    await add_split_bill_participant(split_id, message.from_user.id)
    await message.answer(f"✅ Вы добавлены в чек #{split_id}.")


@router.message(Command("split_bill_paid"))
async def cmd_split_bill_paid(message: Message):
    args = _parse_args(message)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /split_bill_paid <split_id>")
        return

    split_id = int(args[0])
    bill = await get_split_bill(split_id)
    if not bill:
        await message.answer("❌ Событие не найдено.")
        return
    if bill.get("status") != "open":
        await message.answer("⛔ Событие закрыто.")
        return

    participants = await get_split_bill_participants(split_id)
    participant_ids = {int(p["user_id"]) for p in participants}
    if message.from_user.id not in participant_ids:
        await message.answer("❌ Вы не участник этого чека.")
        return

    await mark_split_bill_paid(split_id, message.from_user.id)
    participants = await get_split_bill_participants(split_id)
    if participants and all(bool(p.get("is_paid")) for p in participants):
        try:
            await message.bot.send_message(int(bill["organizer_id"]), "✅ Деньги переведены")
        except Exception:
            pass

    await message.answer("✅ Оплата отмечена.")


@router.message(Command("split_bill_status"))
async def cmd_split_bill_status(message: Message):
    args = _parse_args(message)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /split_bill_status <split_id>")
        return

    split_id = int(args[0])
    bill = await get_split_bill(split_id)
    if not bill:
        await message.answer("❌ Событие не найдено.")
        return

    participants = await get_split_bill_participants(split_id)
    lines = [
        f"💳 Чек #{split_id}",
        f"Статус: {bill.get('status')}",
        f"Сумма: {bill.get('total_amount')}",
        f"Участников: {len(participants)}",
    ]
    for p in participants:
        paid = "✅" if p.get("is_paid") else "⌛"
        lines.append(f"{paid} {p['user_id']}: {p['share_amount']}")

    if message.from_user.id == int(bill.get("organizer_id")) and bill.get("status") == "open":
        lines.append("\\nОрганизатор: можно закрыть только после оплат всех участников: /split_bill_close <id>")

    await message.answer("\\n".join(lines))


@router.message(Command("split_bill_close"))
async def cmd_split_bill_close(message: Message):
    args = _parse_args(message)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /split_bill_close <split_id>")
        return

    split_id = int(args[0])
    bill = await get_split_bill(split_id)
    if not bill:
        await message.answer("❌ Событие не найдено.")
        return
    if int(bill.get("organizer_id")) != message.from_user.id:
        await message.answer("❌ Закрыть событие может только организатор.")
        return

    participants = await get_split_bill_participants(split_id)
    if not participants or any(not bool(p.get("is_paid")) for p in participants):
        await message.answer("❌ Нельзя закрыть: не все участники отметили оплату.")
        return

    await close_split_bill(split_id)
    await message.answer(f"🔒 Чек #{split_id} закрыт.")


@router.message(Command("split_bill_add"))
async def cmd_split_bill_add(message: Message):
    args = _parse_args(message)
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await message.answer("Использование: /split_bill_add <split_id> <user_id>")
        return

    split_id = int(args[0])
    user_id = int(args[1])
    bill = await get_split_bill(split_id)
    if not bill:
        await message.answer("❌ Событие не найдено.")
        return
    if int(bill.get("organizer_id")) != message.from_user.id:
        await message.answer("❌ Добавлять участников может только организатор.")
        return
    if bill.get("status") != "open":
        await message.answer("❌ Событие закрыто.")
        return

    await add_split_bill_participant(split_id, user_id)
    await message.answer(f"✅ Участник {user_id} добавлен в чек #{split_id}.")


@router.message(Command("split_bill_remove"))
async def cmd_split_bill_remove(message: Message):
    args = _parse_args(message)
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await message.answer("Использование: /split_bill_remove <split_id> <user_id>")
        return

    split_id = int(args[0])
    user_id = int(args[1])
    bill = await get_split_bill(split_id)
    if not bill:
        await message.answer("❌ Событие не найдено.")
        return
    if int(bill.get("organizer_id")) != message.from_user.id:
        await message.answer("❌ Удалять участников может только организатор.")
        return
    if bill.get("status") != "open":
        await message.answer("❌ Событие закрыто.")
        return

    await remove_split_bill_participant(split_id, user_id)
    await message.answer(f"🗑 Участник {user_id} удалён из чека #{split_id}.")
