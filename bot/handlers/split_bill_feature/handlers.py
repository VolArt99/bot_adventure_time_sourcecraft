from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.database import is_member_approved
from bot.keyboards import cancel_keyboard, skip_field_keyboard

from .services import (
    add_split_bill_participant,
    close_bill_if_ready,
    finalize_split_bill,
    format_split_bill_text,
    get_split_bill,
    get_split_bill_participants,
    mark_split_bill_paid,
    parse_args,
    refresh_split_message,
    remove_split_bill_participant,
)
from .views import split_bill_create_usage

router = Router(name=__name__)


class SplitBillCreate(StatesGroup):
    title = State()
    amount = State()
    source_event = State()


@router.message(Command("split_bill"))
async def cmd_split_bill(message: Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("❌ Команду /split_bill нужно запускать в личных сообщениях с ботом.")
        return

    await state.set_state(SplitBillCreate.title)
    await message.answer("🧾 Введите название чека:", reply_markup=cancel_keyboard())


@router.message(SplitBillCreate.title, ~F.text.startswith("/"))
async def split_bill_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(SplitBillCreate.amount)
    await message.answer("💰 Введите общую сумму чека (например, 4200):", reply_markup=cancel_keyboard())


@router.message(SplitBillCreate.amount, ~F.text.startswith("/"))
async def split_bill_amount(message: Message, state: FSMContext):
    try:
        amount = float((message.text or "").replace(",", ".").strip())
    except ValueError:
        await message.answer("❌ Сумма должна быть числом, например 4200 или 4200.50")
        return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0.")
        return

    await state.update_data(total_amount=amount)
    await state.set_state(SplitBillCreate.source_event)
    await message.answer(
        "🔗 Укажите ID мероприятия, чтобы автоматически подтянуть участников, или нажмите «Пропустить».",
        reply_markup=skip_field_keyboard("split_event"),
    )


@router.callback_query(SplitBillCreate.source_event, F.data == "skip_split_event")
async def split_bill_skip_event(callback: CallbackQuery, state: FSMContext):
    await state.update_data(source_event_id=None)
    await callback.answer("Связка с мероприятием пропущена")
    await finalize_split_bill(callback.message, state)


@router.message(SplitBillCreate.source_event, ~F.text.startswith("/"))
async def split_bill_source_event(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if raw.lower() == "пропустить":
        await state.update_data(source_event_id=None)
        await finalize_split_bill(message, state)
        return

    if not raw.isdigit():
        await message.answer("❌ Введите числовой event_id или нажмите «Пропустить».")
        return

    await state.update_data(source_event_id=int(raw))
    await finalize_split_bill(message, state)


@router.callback_query(F.data.startswith("sb_join_"))
async def split_bill_join_callback(callback: CallbackQuery):
    split_id = int(callback.data.rsplit("_", 1)[-1])
    if not await is_member_approved(callback.from_user.id):
        await callback.answer("Только участники группы", show_alert=True)
        return

    bill = await get_split_bill(split_id)
    if not bill or bill.get("status") != "open":
        await callback.answer("Чек недоступен", show_alert=True)
        return

    await add_split_bill_participant(split_id, callback.from_user.id)
    await refresh_split_message(callback, split_id)
    await callback.answer("Вы добавлены")


@router.callback_query(F.data.startswith("sb_leave_"))
async def split_bill_leave_callback(callback: CallbackQuery):
    split_id = int(callback.data.rsplit("_", 1)[-1])
    bill = await get_split_bill(split_id)
    if not bill or bill.get("status") != "open":
        await callback.answer("Чек недоступен", show_alert=True)
        return

    if int(bill.get("organizer_id")) == callback.from_user.id:
        await callback.answer("Организатор не может выйти из чека", show_alert=True)
        return

    await remove_split_bill_participant(split_id, callback.from_user.id)
    await refresh_split_message(callback, split_id)
    await callback.answer("Вы удалены")


@router.callback_query(F.data.startswith("sb_paid_"))
async def split_bill_paid_callback(callback: CallbackQuery):
    split_id = int(callback.data.rsplit("_", 1)[-1])
    bill = await get_split_bill(split_id)
    if not bill or bill.get("status") != "open":
        await callback.answer("Чек недоступен", show_alert=True)
        return

    participants = await get_split_bill_participants(split_id)
    participant_ids = {int(p["user_id"]) for p in participants}
    if callback.from_user.id not in participant_ids:
        await callback.answer("Сначала присоединитесь", show_alert=True)
        return

    await mark_split_bill_paid(split_id, callback.from_user.id)
    await refresh_split_message(callback, split_id)
    await callback.answer("Оплата отмечена")


@router.callback_query(F.data.startswith("sb_status_"))
async def split_bill_status_callback(callback: CallbackQuery):
    split_id = int(callback.data.rsplit("_", 1)[-1])
    await refresh_split_message(callback, split_id)
    await callback.answer("Обновлено")


@router.callback_query(F.data.startswith("sb_close_"))
async def split_bill_close_callback(callback: CallbackQuery):
    split_id = int(callback.data.rsplit("_", 1)[-1])
    bill = await get_split_bill(split_id)
    if not bill:
        await callback.answer("Чек не найден", show_alert=True)
        return
    if int(bill.get("organizer_id")) != callback.from_user.id:
        await callback.answer("Только организатор", show_alert=True)
        return

    if not await close_bill_if_ready(split_id):
        await callback.answer("Не все участники оплатили", show_alert=True)
        return

    await refresh_split_message(callback, split_id)
    await callback.answer("Чек закрыт")


@router.message(Command("split_bill_create"))
async def cmd_split_bill_create(message: Message):
    args = parse_args(message)
    if not args:
        await message.answer(split_bill_create_usage())
        return

    try:
        amount = float(args[0])
    except ValueError:
        await message.answer("❌ Сумма должна быть числом.")
        return

    source_event_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    split_id = await create_split_bill_legacy(
        message=message,
        amount=amount,
        source_event_id=source_event_id,
    )
    await message.answer(f"✅ Создано событие разделения чека #{split_id}.\nДальше используйте: /split_bill_status {split_id}")


async def create_split_bill_legacy(message: Message, amount: float, source_event_id: int | None) -> int:
    from bot.config import GROUP_ID
    from bot.database import create_split_bill, get_event_participant_ids

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
    return split_id


@router.message(Command("split_bill_join"))
async def cmd_split_bill_join(message: Message):
    args = parse_args(message)
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
    args = parse_args(message)
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
    await message.answer("✅ Оплата отмечена.")


@router.message(Command("split_bill_status"))
async def cmd_split_bill_status(message: Message):
    args = parse_args(message)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /split_bill_status <split_id>")
        return

    split_id = int(args[0])
    text = await format_split_bill_text(split_id, message.bot)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("split_bill_close"))
async def cmd_split_bill_close(message: Message):
    args = parse_args(message)
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

    if not await close_bill_if_ready(split_id):
        await message.answer("❌ Нельзя закрыть: не все участники отметили оплату.")
        return
    await message.answer(f"🔒 Чек #{split_id} закрыт.")


@router.message(Command("split_bill_add"))
async def cmd_split_bill_add(message: Message):
    args = parse_args(message)
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
    args = parse_args(message)
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
