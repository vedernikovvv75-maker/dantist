"""
Демо записи на приём: выбор даты/периода → подтверждение. Тег услуги в context.user_data['appointment_tag'].
"""
from telegram import Update
from telegram.ext import ContextTypes

from db import add_funnel_event, update_user
from texts import APPOINTMENT_START, APPOINTMENT_CONFIRM
from patient_menu import get_main_keyboard

STATE_WAIT_DATE = "app_wait_date"


async def start_patient_flow(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    from_query=None,
) -> None:
    context.user_data["appointment_state"] = STATE_WAIT_DATE
    tag = context.user_data.get("appointment_tag", "consult")
    add_funnel_event(update.effective_user.id, "appointment_start", tag)
    msg = (update.message if update.message else (from_query and from_query.message))
    if not msg:
        return
    await msg.reply_text(APPOINTMENT_START)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    state = context.user_data.get("appointment_state")
    if state != STATE_WAIT_DATE:
        return False
    user = update.effective_user
    preferred = (update.message.text or "").strip()
    context.user_data.pop("appointment_state", None)
    tag = context.user_data.pop("appointment_tag", "consult")
    add_funnel_event(user.id, "appointment_submitted", f"{tag}:{preferred}")
    update_user(user.id, status="booked")
    await update.message.reply_text(APPOINTMENT_CONFIRM, reply_markup=get_main_keyboard())
    return True
