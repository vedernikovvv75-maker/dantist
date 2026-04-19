"""
Услуги и цены, акция месяца. Разделы: гигиена, ортодонтия, имплантация, детская.
Кнопка «Подобрать время» → сценарий записи с тегом услуги.
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import add_funnel_event
from texts import (
    CATALOG_ROOT,
    BTN_CATALOG_HYGIENE,
    BTN_CATALOG_ORTHO,
    BTN_CATALOG_IMPLANT,
    BTN_CATALOG_KIDS,
    PROMO_MONTH,
    BTN_BOOK_TIME,
    BTN_PROMO_DETAILS,
    BTN_BOOK_PROMO,
)
from patient_menu import get_main_keyboard

# Акция месяца (шаблон)
PROMO_TITLE = "Профессиональная чистка зубов со скидкой 50%"
PROMO_END_DATE = "28.03.2025"


def _catalog_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_CATALOG_HYGIENE, callback_data="cat_hygiene")],
        [InlineKeyboardButton(BTN_CATALOG_ORTHO, callback_data="cat_ortho")],
        [InlineKeyboardButton(BTN_CATALOG_IMPLANT, callback_data="cat_implant")],
        [InlineKeyboardButton(BTN_CATALOG_KIDS, callback_data="cat_kids")],
    ])


async def show_root(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(CATALOG_ROOT, reply_markup=_catalog_keyboard())
    else:
        await update.callback_query.message.reply_text(CATALOG_ROOT, reply_markup=_catalog_keyboard())


async def show_promo_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    from_query=None,
) -> None:
    text = PROMO_MONTH.format(date=PROMO_END_DATE, title=PROMO_TITLE)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_BOOK_PROMO, callback_data="book_tag_promo")],
        [InlineKeyboardButton(BTN_PROMO_DETAILS, callback_data="promo_details")],
    ])
    if from_query:
        await from_query.message.reply_text(text, reply_markup=keyboard)
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    data = query.data
    if not data or not data.startswith(("cat_", "book_tag_", "promo_")):
        return False
    await query.answer()
    user = query.from_user
    if data == "cat_hygiene":
        add_funnel_event(user.id, "catalog_open", "hygiene")
        await query.message.reply_text(
            "Гигиена и профилактика: профессиональная чистка, снятие камня, фторирование. "
            "Частые вопросы: как часто делать чистку? — раз в 6–12 месяцев; больно ли? — обычно нет, при чувствительности применяют гель.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BTN_BOOK_TIME, callback_data="book_tag_hygiene")],
            ]),
        )
        return True
    if data == "cat_ortho":
        add_funnel_event(user.id, "catalog_open", "ortho")
        from ortho import show_root as ortho_show
        await ortho_show(update, context)
        return True
    if data == "cat_implant":
        add_funnel_event(user.id, "catalog_open", "implant")
        await query.message.reply_text(
            "Имплантация и протезирование: установка имплантов, коронки, мосты. "
            "Частые вопросы: срок службы? — при правильном уходе десятилетия; есть ли рассрочка? — да.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BTN_BOOK_TIME, callback_data="book_tag_implant")],
            ]),
        )
        return True
    if data == "cat_kids":
        add_funnel_event(user.id, "catalog_open", "kids")
        await query.message.reply_text(
            "Детская стоматология: адаптация, лечение кариеса, профилактика. "
            "Частые вопросы: с какого возраста? — с 2–3 лет на осмотр; как подготовить ребёнка? — расскажем при записи.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BTN_BOOK_TIME, callback_data="book_tag_kids")],
            ]),
        )
        return True
    if data == "promo_details":
        await query.message.reply_text(
            "Чистка включает: снятие налёта и камня, полировку, при необходимости фторирование. Длительность около часа.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BTN_BOOK_PROMO, callback_data="book_tag_promo")],
            ]),
        )
        return True
    if data.startswith("book_tag_"):
        tag = data.replace("book_tag_", "")
        context.user_data["appointment_tag"] = tag
        from demo_appointment import start_patient_flow
        await start_patient_flow(update, context, from_query=query)
        return True
    return False
