"""
Главное меню пациента «Улыбка+»: приветствие и 6 кнопок. Роутинг по нажатиям в handlers.
"""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from config import DEMO_SWITCH_ENABLED
from texts import (
    PATIENT_GREETING,
    BTN_BONUS_CARD,
    BTN_BOOK_CONSULT,
    BTN_EMERGENCY,
    BTN_SERVICES,
    BTN_DOCTORS,
    BTN_IMPLANT14,
)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_BONUS_CARD)],
        [KeyboardButton(BTN_BOOK_CONSULT)],
        [KeyboardButton(BTN_EMERGENCY)],
        [KeyboardButton(BTN_SERVICES)],
        [KeyboardButton(BTN_DOCTORS)],
        [KeyboardButton(BTN_IMPLANT14)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def show_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    from_query=None,
) -> None:
    text = PATIENT_GREETING
    if DEMO_SWITCH_ENABLED:
        text += "\n\nВ демо: перейти в режим заказчика — /owner"
    reply_markup = get_main_keyboard()
    if from_query:
        await from_query.message.reply_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        raise ValueError("show_main_menu: need update.message or from_query")


def is_main_menu_button(text: str) -> bool:
    return text in (
        BTN_BONUS_CARD,
        BTN_BOOK_CONSULT,
        BTN_EMERGENCY,
        BTN_SERVICES,
        BTN_DOCTORS,
        BTN_IMPLANT14,
    )
