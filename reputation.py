"""
Репутационный контент: врачи, отзывы, рейтинги. Контекст пациента.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import SITE_URL
from db import add_funnel_event
from texts import (
    REPUTATION_ROOT,
    BTN_REVIEWS_SITE,
    BTN_REVIEWS_PRODOCTOR,
    BTN_BOOK_DOCTOR,
    BTN_DOCTOR_REVIEWS,
)
from patient_menu import get_main_keyboard

PRODOCTOR_URL = "https://prodoctorov.ru/"


def _root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(BTN_REVIEWS_SITE, url=SITE_URL or "https://example.com"),
            InlineKeyboardButton(BTN_REVIEWS_PRODOCTOR, url=PRODOCTOR_URL),
        ],
        [InlineKeyboardButton("Карточки врачей", callback_data="rep_doctors")],
    ])


async def show_root(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    add_funnel_event(update.effective_user.id, "reputation_open")
    msg = update.message or (update.callback_query and update.callback_query.message)
    if not msg:
        return
    await msg.reply_text(
        REPUTATION_ROOT,
        reply_markup=_root_keyboard(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    data = query.data
    if not data or not data.startswith("rep_"):
        return False
    await query.answer()
    if data == "rep_doctors":
        await query.message.reply_text(
            "Демо: карточка врача.\n\n"
            "Иванова Анна Петровна — ортодонт. Стаж 12 лет. "
            "Узкая специализация: исправление прикуса элайнерами, сложные случаи.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BTN_DOCTOR_REVIEWS, url=PRODOCTOR_URL)],
                [InlineKeyboardButton(BTN_BOOK_DOCTOR, callback_data="book_tag_doctor")],
            ]),
        )
        return True
    if data == "book_tag_doctor":
        context.user_data["appointment_tag"] = "doctor"
        from demo_appointment import start_patient_flow
        await start_patient_flow(update, context, from_query=query)
        return True
    return False
