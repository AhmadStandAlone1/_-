import logging

from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)

from config import get_config  # Corrected import statement
from keyboards import Keyboards

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
ADMIN_BAN_USER = 1
ADMIN_UNBAN_USER = 2
ADMIN_MODIFY_BALANCE = 3

# Keyboards
keyboards = Keyboards()


async def ban_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the ban user conversation."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "أدخل معرف المستخدم الذي تريد حظره:",
        reply_markup=keyboards.cancel_keyboard()
    )
    return ADMIN_BAN_USER


async def unban_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the unban user conversation."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "أدخل معرف المستخدم الذي تريد إزالة الحظر عنه:",
        reply_markup=keyboards.cancel_keyboard()
    )
    return ADMIN_UNBAN_USER


async def modify_balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the modify balance conversation."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "أدخل معرف المستخدم الذي تريد تعديل رصيده:",
        reply_markup=keyboards.cancel_keyboard()
    )
    return ADMIN_MODIFY_BALANCE


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user input for ban, unban, and modify balance."""
    user_input = update.message.text
    context.user_data['user_input'] = user_input

    state = context.chat_data.get('state')  # Retrieve the state from chat_data

    if state == ADMIN_BAN_USER:
        await update.message.reply_text(
            f"تم حظر المستخدم {user_input} بنجاح.",
            reply_markup=keyboards.admin_keyboard()
        )
    elif state == ADMIN_UNBAN_USER:
        await update.message.reply_text(
            f"تم إزالة الحظر عن المستخدم {user_input} بنجاح.",
            reply_markup=keyboards.admin_keyboard()
        )
    elif state == ADMIN_MODIFY_BALANCE:
        await update.message.reply_text(
            f"تم تعديل رصيد المستخدم {user_input} بنجاح.",
            reply_markup=keyboards.admin_keyboard()
        )
    else:
        await update.message.reply_text(
            "حدث خطأ: لم يتم تحديد الحالة.",
            reply_markup=keyboards.admin_keyboard()
        )

    return ConversationHandler.END


async def edit_rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edits the exchange rate based on the selected currency."""
    query = update.callback_query
    await query.answer()

    currency = query.data.split('_')[-1]  # Extract currency from callback data
    context.user_data['currency'] = currency  # Store currency in user_data

    await query.edit_message_text(
        f"أدخل سعر الصرف الجديد لـ {currency}:",
        reply_markup=keyboards.cancel_keyboard()
    )
    return 4  # Assuming 4 is the state for WAITING_FOR_RATE


async def handle_rate_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the update of the exchange rate."""
    new_rate = update.message.text
    currency = context.user_data.get('currency')

    if currency == 'USD':
        config = get_config()
        success = config.update_usd_rate(new_rate)
        if success:
            await update.message.reply_text(
                f"تم تحديث سعر صرف الدولار إلى {new_rate} بنجاح.",
                reply_markup=keyboards.admin_keyboard()
            )
        else:
            await update.message.reply_text(
                "حدث خطأ أثناء تحديث سعر صرف الدولار.",
                reply_markup=keyboards.admin_keyboard()
            )
    elif currency == 'USDT':
        config = get_config()
        success = config.update_usdt_rate(new_rate)
        if success:
            await update.message.reply_text(
                f"تم تحديث سعر صرف USDT إلى {new_rate} بنجاح.",
                reply_markup=keyboards.admin_keyboard()
            )
        else:
            await update.message.reply_text(
                "حدث خطأ أثناء تحديث سعر صرف USDT.",
                reply_markup=keyboards.admin_keyboard()
            )
    else:
        await update.message.reply_text(
            "حدث خطأ: لم يتم تحديد العملة.",
            reply_markup=keyboards.admin_keyboard()
        )

    return ConversationHandler.END