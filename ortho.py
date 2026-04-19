"""
Ортодонтия: «Исправьте прикус без переплат — рассрочка 0%».
Ветки: для взрослого / ребёнка / элайнеры → краткий текст + запись на консультацию.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import add_funnel_event
from texts import (
    ORTHO_OFFER,
    BTN_ORTHO_ADULT,
    BTN_ORTHO_KID,
    BTN_ORTHO_ALIGNERS,
    ORTHO_ADULT_TEXT,
    ORTHO_KID_TEXT,
    ORTHO_ALIGNERS_TEXT,
    BTN_ORTHO_BOOK,
)
from patient_menu import get_main_keyboard


def _root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_ORTHO_ADULT, callback_data="ortho_adult")],
        [InlineKeyboardButton(BTN_ORTHO_KID, callback_data="ortho_kid")],
        [InlineKeyboardButton(BTN_ORTHO_ALIGNERS, callback_data="ortho_aligners")],
    ])


async def show_root(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message or (update.callback_query and update.callback_query.message)
    if not msg:
        return
    await msg.reply_text(ORTHO_OFFER, reply_markup=_root_keyboard())


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    data = query.data
    if not data or not data.startswith("ortho_"):
        return False
    await query.answer()
    user = query.from_user
    add_funnel_event(user.id, "ortho_open", data)
    if data == "ortho_adult":
        text = ORTHO_ADULT_TEXT
    elif data == "ortho_kid":
        text = ORTHO_KID_TEXT
    elif data == "ortho_aligners":
        text = ORTHO_ALIGNERS_TEXT
    else:
        return True
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_ORTHO_BOOK, callback_data="book_tag_ortho")],
    ])
    await query.message.reply_text(text, reply_markup=keyboard)
    return True
