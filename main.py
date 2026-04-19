"""
Демо-бот «Улыбка+» для стоматологических клиник. Запуск: python main.py
Спека: SPEC_ulybka_plus.md
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, DEMO_SWITCH_ENABLED
from db import init_db
from start import handle_start, handle_qualification_callback, handle_patient, handle_owner
from patient_menu import show_main_menu, get_main_keyboard, is_main_menu_button
from texts import (
    BTN_BONUS_CARD,
    BTN_BOOK_CONSULT,
    BTN_EMERGENCY,
    BTN_SERVICES,
    BTN_DOCTORS,
    BTN_IMPLANT14,
)
import bonus_card
import emergency
import catalog
import ortho
import reputation
import implant14
import demo_appointment

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.callback_query.data
    if data.startswith("qual_"):
        await handle_qualification_callback(update, context)
        return
    if await bonus_card.handle_callback(update, context):
        return
    if await emergency.handle_callback(update, context):
        return
    if await catalog.handle_callback(update, context):
        return
    if await ortho.handle_callback(update, context):
        return
    if await reputation.handle_callback(update, context):
        return
    if await implant14.handle_callback(update, context):
        return
    logger.warning("Unhandled callback_data: %s", data)


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        if update.message and (update.message.photo or update.message.document):
            if context.user_data.get("emergency_wait_photo"):
                await update.message.reply_text(
                    "Фото принято. Администратор свяжется с вами.",
                    reply_markup=get_main_keyboard(),
                )
                context.user_data.pop("emergency_wait_photo", None)
                context.user_data.pop("emergency_state", None)
            return
        return
    text = update.message.text.strip()
    if await bonus_card.handle_message(update, context):
        return
    if await emergency.handle_message(update, context):
        return
    if await demo_appointment.handle_message(update, context):
        return
    if is_main_menu_button(text):
        if text == BTN_BONUS_CARD:
            await bonus_card.start_flow(update, context)
        elif text == BTN_BOOK_CONSULT:
            context.user_data["appointment_tag"] = "consult"
            await demo_appointment.start_patient_flow(update, context)
        elif text == BTN_EMERGENCY:
            await emergency.start_flow(update, context)
        elif text == BTN_SERVICES:
            await catalog.show_root(update, context)
        elif text == BTN_DOCTORS:
            await reputation.show_root(update, context)
        elif text == BTN_IMPLANT14:
            await implant14.start_flow(update, context)
        return
    await update.message.reply_text(
        "Выберите пункт меню ниже или отправьте /start.",
        reply_markup=get_main_keyboard(),
    )


def main() -> None:
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    if DEMO_SWITCH_ENABLED:
        app.add_handler(CommandHandler("patient", handle_patient))
        app.add_handler(CommandHandler("owner", handle_owner))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, message_router))
    app.add_handler(MessageHandler(filters.CONTACT, message_router))
    print("Демо-бот «Улыбка+» запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
