"""
Экстренные пациенты: FSM — выбор типа проблемы → безопасный совет → звонок / отправить фото.
Ночной режим по времени — круглосуточная линия + «Попросить перезвонить».
"""
from datetime import datetime, time as dt_time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from config import CLINIC_PHONE
from db import add_funnel_event
from texts import (
    EMERGENCY_CHOOSE,
    BTN_EMERGENCY_PAIN,
    BTN_EMERGENCY_SWELLING,
    BTN_EMERGENCY_CHIP,
    BTN_EMERGENCY_BLEEDING,
    EMERGENCY_SAFE_ADVICE,
    BTN_CALL_CLINIC,
    BTN_SEND_PHOTO_DOC,
    EMERGENCY_PHOTO_RECEIVED,
    EMERGENCY_NIGHT,
    BTN_REQUEST_CALLBACK,
)
from patient_menu import get_main_keyboard

STATE_CHOOSE, STATE_AFTER_ADVICE = "em_choose", "em_after"

NIGHT_START = dt_time(23, 0)
NIGHT_END = dt_time(7, 0)


def _is_night() -> bool:
    now = datetime.now().time()
    if NIGHT_START > NIGHT_END:
        return now >= NIGHT_START or now < NIGHT_END
    return NIGHT_START <= now < NIGHT_END


def _keyboard_choose() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_EMERGENCY_PAIN, callback_data="em_pain")],
        [InlineKeyboardButton(BTN_EMERGENCY_SWELLING, callback_data="em_swelling")],
        [InlineKeyboardButton(BTN_EMERGENCY_CHIP, callback_data="em_chip")],
        [InlineKeyboardButton(BTN_EMERGENCY_BLEEDING, callback_data="em_bleeding")],
    ])


def _keyboard_after_advice() -> InlineKeyboardMarkup:
    # Telegram не поддерживает url=tel: в inline-кнопках — показываем номер по нажатию
    row = [InlineKeyboardButton(BTN_CALL_CLINIC, callback_data="em_show_phone")]
    if _is_night():
        row.append(InlineKeyboardButton(BTN_REQUEST_CALLBACK, callback_data="em_callback"))
    return InlineKeyboardMarkup([
        row,
        [InlineKeyboardButton(BTN_SEND_PHOTO_DOC, callback_data="em_send_photo")],
    ])


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["emergency_state"] = STATE_CHOOSE
    add_funnel_event(update.effective_user.id, "emergency_start")
    await update.message.reply_text(EMERGENCY_CHOOSE, reply_markup=_keyboard_choose())


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    data = query.data
    if not data or not data.startswith("em_"):
        return False
    await query.answer()
    user = query.from_user
    if data == "em_send_photo":
        context.user_data["emergency_state"] = STATE_AFTER_ADVICE
        context.user_data["emergency_wait_photo"] = True
        await query.message.reply_text(
            "Отправьте фото или описание ситуации — администратор свяжется с вами.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Отмена", request_location=False)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return True
    if data == "em_callback":
        await query.message.reply_text(
            "Заявка на перезвон принята. С вами свяжутся в ближайшее время.",
            reply_markup=get_main_keyboard(),
        )
        for k in ("emergency_state", "emergency_type", "emergency_wait_photo"):
            context.user_data.pop(k, None)
        return True
    if data == "em_show_phone":
        await query.message.reply_text(f"Телефон клиники: {CLINIC_PHONE}\n\nНажмите на номер для звонка (в мобильном приложении).")
        return True
    # em_pain, em_swelling, em_chip, em_bleeding
    context.user_data["emergency_type"] = data
    context.user_data["emergency_state"] = STATE_AFTER_ADVICE
    add_funnel_event(user.id, "emergency_type", data)
    text = EMERGENCY_SAFE_ADVICE
    if _is_night():
        text += "\n\n" + EMERGENCY_NIGHT.format(phone=CLINIC_PHONE)
    await query.message.reply_text(text, reply_markup=_keyboard_after_advice())
    return True


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    state = context.user_data.get("emergency_state")
    if state != STATE_AFTER_ADVICE or not context.user_data.get("emergency_wait_photo"):
        return False
    if (update.message.text or "").strip() == "Отмена":
        for k in ("emergency_state", "emergency_type", "emergency_wait_photo"):
            context.user_data.pop(k, None)
        await update.message.reply_text("Отменено.", reply_markup=get_main_keyboard())
        return True
    add_funnel_event(update.effective_user.id, "emergency_photo_sent")
    context.user_data.pop("emergency_wait_photo", None)
    await update.message.reply_text(EMERGENCY_PHOTO_RECEIVED, reply_markup=get_main_keyboard())
    return True
