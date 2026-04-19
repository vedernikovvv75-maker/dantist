"""
Имплантация за 14 дней: УТП → мини-тест из 3 вопросов Да/Нет → результат и возражения.
Запись с тегом IMPLANT14.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import add_funnel_event
from texts import (
    IMPLANT14_OFFER,
    BTN_IMPLANT_SUIT,
    BTN_IMPLANT_PRICE,
    BTN_IMPLANT_BOOK,
    IMPLANT_Q1,
    IMPLANT_Q2,
    IMPLANT_Q3,
    BTN_YES,
    BTN_NO,
    IMPLANT_RESULT_YES,
    IMPLANT_RESULT_NO,
    BTN_OBJECTION_PRICE,
    BTN_OBJECTION_SAFE,
    BTN_OBJECTION_PAIN,
    IMPLANT_OBJECTION_PRICE,
    IMPLANT_OBJECTION_SAFE,
    IMPLANT_OBJECTION_PAIN,
)
from patient_menu import get_main_keyboard

STATE_OFFER, STATE_Q1, STATE_Q2, STATE_Q3, STATE_RESULT, STATE_OBJECTION = (
    "im_offer", "im_q1", "im_q2", "im_q3", "im_result", "im_objection"
)


def _offer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_IMPLANT_SUIT, callback_data="im_suit")],
        [InlineKeyboardButton(BTN_IMPLANT_PRICE, callback_data="im_price")],
        [InlineKeyboardButton(BTN_IMPLANT_BOOK, callback_data="im_book")],
    ])


def _yes_no_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(BTN_YES, callback_data="im_yes"),
            InlineKeyboardButton(BTN_NO, callback_data="im_no"),
        ],
    ])


def _result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Записаться на консультацию", callback_data="im_book")],
        [InlineKeyboardButton("Задать вопрос врачу", callback_data="im_question")],
    ])


def _objection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_OBJECTION_PRICE, callback_data="im_obj_price")],
        [InlineKeyboardButton(BTN_OBJECTION_SAFE, callback_data="im_obj_safe")],
        [InlineKeyboardButton(BTN_OBJECTION_PAIN, callback_data="im_obj_pain")],
        [InlineKeyboardButton(BTN_IMPLANT_BOOK, callback_data="im_book")],
    ])


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["implant_state"] = STATE_OFFER
    context.user_data["implant_yes_count"] = 0
    add_funnel_event(update.effective_user.id, "implant14_start")
    await update.message.reply_text(IMPLANT14_OFFER, reply_markup=_offer_keyboard())


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    data = query.data
    if not data or not data.startswith("im_"):
        return False
    await query.answer()
    user = query.from_user
    state = context.user_data.get("implant_state", STATE_OFFER)

    if data == "im_price":
        await query.message.reply_text(
            "Стоимость подбирается после консультации и 3D-диагностики. Есть рассрочка. Записаться на бесплатную консультацию?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BTN_IMPLANT_BOOK, callback_data="im_book")],
            ]),
        )
        return True
    if data == "im_book":
        context.user_data["appointment_tag"] = "IMPLANT14"
        for k in ("implant_state", "implant_yes_count"):
            context.user_data.pop(k, None)
        from demo_appointment import start_patient_flow
        await start_patient_flow(update, context, from_query=query)
        return True
    if data == "im_question":
        await query.message.reply_text(
            "Напишите ваш вопрос в чат — администратор передаст врачу и ответит.",
            reply_markup=get_main_keyboard(),
        )
        return True

    if data == "im_suit":
        context.user_data["implant_state"] = STATE_Q1
        context.user_data["implant_yes_count"] = 0
        await query.message.reply_text(IMPLANT_Q1, reply_markup=_yes_no_keyboard())
        return True

    if data in ("im_yes", "im_no") and state in (STATE_Q1, STATE_Q2, STATE_Q3):
        if data == "im_yes":
            context.user_data["implant_yes_count"] = context.user_data.get("implant_yes_count", 0) + 1
        if state == STATE_Q1:
            context.user_data["implant_state"] = STATE_Q2
            await query.message.reply_text(IMPLANT_Q2, reply_markup=_yes_no_keyboard())
        elif state == STATE_Q2:
            context.user_data["implant_state"] = STATE_Q3
            await query.message.reply_text(IMPLANT_Q3, reply_markup=_yes_no_keyboard())
        else:
            context.user_data["implant_state"] = STATE_RESULT
            yes_count = context.user_data.get("implant_yes_count", 0)
            if yes_count >= 2:
                await query.message.reply_text(
                    IMPLANT_RESULT_YES,
                    reply_markup=_result_keyboard(),
                )
            else:
                await query.message.reply_text(
                    IMPLANT_RESULT_NO,
                    reply_markup=_result_keyboard(),
                )
        return True

    if data.startswith("im_obj_"):
        if data == "im_obj_price":
            await query.message.reply_text(IMPLANT_OBJECTION_PRICE, reply_markup=_objection_keyboard())
        elif data == "im_obj_safe":
            await query.message.reply_text(IMPLANT_OBJECTION_SAFE, reply_markup=_objection_keyboard())
        elif data == "im_obj_pain":
            await query.message.reply_text(IMPLANT_OBJECTION_PAIN, reply_markup=_objection_keyboard())
        return True

    return False
