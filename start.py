"""
Старт и квалификация: собственник vs пациент. При первом /start — экран квалификации.
Если is_owner=True — owner-flow, иначе patient_menu.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import get_user, add_user, set_owner, add_funnel_event
from texts import (
    QUALIFICATION_PROMPT,
    BTN_OWNER_YES,
    BTN_OWNER_NO,
    OWNER_FLOW_WELCOME,
)
from patient_menu import show_main_menu


def get_qualification_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_OWNER_YES, callback_data="qual_owner_yes")],
        [InlineKeyboardButton(BTN_OWNER_NO, callback_data="qual_owner_no")],
    ])


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    existing = get_user(user.id)
    if not existing:
        add_user(user_id=user.id, username=user.username, first_name=user.first_name)
        add_funnel_event(user.id, "qualification_shown")
        await update.message.reply_text(
            QUALIFICATION_PROMPT,
            reply_markup=get_qualification_keyboard(),
        )
        return
    is_owner_flag = existing[5] if len(existing) > 5 else 0
    if is_owner_flag:
        await _owner_flow(update, context)
    else:
        await show_main_menu(update, context)


async def handle_qualification_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if not user:
        return
    data = query.data
    if data == "qual_owner_yes":
        set_owner(user.id, True)
        add_funnel_event(user.id, "qualification_owner")
        await query.message.reply_text(OWNER_FLOW_WELCOME)
        # Повторный /start будет вести сюда же — в full версии здесь меню owner-flow
    elif data == "qual_owner_no":
        set_owner(user.id, False)
        add_funnel_event(user.id, "qualification_patient")
        await show_main_menu(update, context, from_query=query)


async def handle_patient(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /patient — переключить текущего пользователя в режим пациента и показать меню."""
    user = update.effective_user
    if not user:
        return
    existing = get_user(user.id)
    if not existing:
        add_user(user_id=user.id, username=user.username, first_name=user.first_name)
    set_owner(user.id, False)
    add_funnel_event(user.id, "switch_to_patient")
    await show_main_menu(update, context)


async def handle_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /owner — переключить в режим заказчика/собственника (только для демо)."""
    user = update.effective_user
    if not user:
        return
    existing = get_user(user.id)
    if not existing:
        add_user(user_id=user.id, username=user.username, first_name=user.first_name)
    set_owner(user.id, True)
    add_funnel_event(user.id, "switch_to_owner")
    await _owner_flow(update, context)


async def _owner_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(OWNER_FLOW_WELCOME)
    else:
        await update.callback_query.message.reply_text(OWNER_FLOW_WELCOME)
