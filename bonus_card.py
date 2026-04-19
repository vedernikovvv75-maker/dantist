"""
Воронка «Бонусная карта на год»: оффер → имя → телефон → согласие → активация.
После активации — меню: Акция месяца / Записаться с картой / Что по моей проблеме?
"""
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from db import get_user, activate_bonus_card, add_funnel_event
from texts import (
    BONUS_CARD_OFFER,
    BTN_GET_CARD,
    BTN_CARD_DETAILS,
    BONUS_CARD_ASK_NAME,
    BONUS_CARD_ASK_PHONE,
    BTN_SEND_PHONE,
    BONUS_CARD_CONSENT,
    BTN_CONSENT,
    BONUS_CARD_ACTIVATED,
    BTN_ACTION_MONTH,
    BTN_BOOK_WITH_CARD,
    BTN_MY_PROBLEM,
)
from patient_menu import get_main_keyboard

STATE_OFFER, STATE_NAME, STATE_PHONE, STATE_CONSENT = "bc_offer", "bc_name", "bc_phone", "bc_consent"


def _card_post_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_ACTION_MONTH, callback_data="card_action_month")],
        [InlineKeyboardButton(BTN_BOOK_WITH_CARD, callback_data="card_book")],
        [InlineKeyboardButton(BTN_MY_PROBLEM, callback_data="card_my_problem")],
    ])


def get_offer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_GET_CARD, callback_data="bonus_get_card")],
        [InlineKeyboardButton(BTN_CARD_DETAILS, callback_data="bonus_details")],
    ])


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_SEND_PHONE, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_CONSENT, callback_data="bonus_consent")],
    ])


def _gen_card_number(user_id: int) -> str:
    return f"UP-{user_id % 100000:05d}"


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["bonus_state"] = STATE_OFFER
    add_funnel_event(update.effective_user.id, "bonus_card_start")
    await update.message.reply_text(
        BONUS_CARD_OFFER,
        reply_markup=get_offer_keyboard(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обрабатывает callback по бонусной карте. Возвращает True если обработано."""
    query = update.callback_query
    data = query.data
    if data == "bonus_details":
        await query.answer("Карта действует 12 месяцев, скидки до 20%, спецпредложения по SMS/Telegram.")
        return True
    if data == "bonus_get_card":
        await query.answer()
        context.user_data["bonus_state"] = STATE_NAME
        await query.message.reply_text(BONUS_CARD_ASK_NAME)
        return True
    if data == "bonus_consent":
        await query.answer()
        user = query.from_user
        if not user:
            return True
        phone = context.user_data.get("bonus_phone", "")
        card_number = _gen_card_number(user.id)
        activate_bonus_card(user.id, card_number, phone)
        add_funnel_event(user.id, "bonus_card_activated", card_number)
        for key in ("bonus_state", "bonus_name", "bonus_phone"):
            context.user_data.pop(key, None)
        text = BONUS_CARD_ACTIVATED.format(card_number=card_number)
        await query.message.reply_text(text, reply_markup=_card_post_keyboard())
        return True
    if data == "card_action_month":
        await query.answer()
        from catalog import show_promo_month
        await show_promo_month(update, context, from_query=query)
        return True
    if data == "card_book":
        await query.answer()
        from demo_appointment import start_patient_flow
        await start_patient_flow(update, context, from_query=query)
        return True
    if data == "card_my_problem":
        await query.answer()
        await query.message.reply_text(
            "Напишите коротко, что вас беспокоит (например: больной зуб, отбеливание), и мы подберём услугу.",
            reply_markup=get_main_keyboard(),
        )
        return True
    return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обрабатывает текст/контакт в рамках воронки бонусной карты. Возвращает True если обработано."""
    state = context.user_data.get("bonus_state")
    if not state:
        return False
    if state == STATE_NAME:
        name = (update.message.text or "").strip()
        if len(name) < 2:
            await update.message.reply_text("Введите, пожалуйста, имя (минимум 2 символа).")
            return True
        context.user_data["bonus_name"] = name
        context.user_data["bonus_state"] = STATE_PHONE
        await update.message.reply_text(BONUS_CARD_ASK_PHONE, reply_markup=get_phone_keyboard())
        return True
    if state == STATE_PHONE:
        phone = None
        if update.message.contact:
            phone = update.message.contact.phone_number or ""
        if not phone and update.message.text:
            raw = re.sub(r"\D", "", update.message.text)
            if len(raw) >= 10:
                phone = "+7" + raw[-10:] if len(raw) == 10 else raw
        if not phone:
            await update.message.reply_text(
                "Отправьте номер телефона кнопкой ниже или введите цифрами.",
                reply_markup=get_phone_keyboard(),
            )
            return True
        context.user_data["bonus_phone"] = phone
        context.user_data["bonus_state"] = STATE_CONSENT
        await update.message.reply_text(
            BONUS_CARD_CONSENT,
            reply_markup=get_consent_keyboard(),
        )
        return True
    return False
