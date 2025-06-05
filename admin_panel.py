import logging
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import Keyboards
from handlers import is_admin, EDITING_ENV_VALUE, HANDLE_SYRIATEL_NUMBERS, HANDLE_USDT_WALLETS

# Logger
logger = logging.getLogger(__name__)

class AdminPanel:
    """Handles admin-related functionalities."""

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the admin panel."""
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("🚫 ليس لديك صلاحيات المسؤول")
            return ConversationHandler.END

        if update.message:
            await update.message.reply_text(
                "⚙️ لوحة التحكم",
                reply_markup=Keyboards.admin_panel()
            )
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.message.edit_text(
                "⚙️ لوحة التحكم",
                reply_markup=Keyboards.admin_panel()
            )
        return ConversationHandler.END

    async def admin_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the admin settings menu."""
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("🚫 ليس لديك صلاحيات المسؤول")
            return ConversationHandler.END

        buttons = [
            [
                InlineKeyboardButton("📝 تعديل متغيرات .env", callback_data="edit_env"),
                InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")
            ]
        ]

        if update.message:
            await update.message.reply_text(
                "⚙️ إعدادات عامة",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.message.edit_text(
                "⚙️ إعدادات عامة",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        return ConversationHandler.END

    async def edit_env_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the edit .env settings menu."""
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("🚫 ليس لديك صلاحيات المسؤول")
            return ConversationHandler.END

        buttons = [
            [
                InlineKeyboardButton("📱 أرقام سيرياتيل كاش", callback_data="edit_syriatel_numbers"),
                InlineKeyboardButton("💰 محافظ USDT", callback_data="edit_usdt_wallets")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings")]
        ]

        if update.message:
            await update.message.reply_text(
                "📝 تعديل متغيرات .env",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.message.edit_text(
                "📝 تعديل متغيرات .env",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        return ConversationHandler.END

    async def edit_syriatel_numbers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit Syriatel Cash numbers."""
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("🚫 ليس لديك صلاحيات المسؤول")
            return ConversationHandler.END

        context.user_data['editing_env_var'] = 'syriatel'

        if update.message:
            await update.message.reply_text(
                "📱 أرسل أرقام سيرياتيل كاش الجديدة (مفصولة بفواصل)",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 إلغاء", callback_data="admin_settings")
                ]])
            )
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.message.edit_text(
                "📱 أرسل أرقام سيرياتيل كاش الجديدة (مفصولة بفواصل)",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 إلغاء", callback_data="admin_settings")
                ]])
            )
        return HANDLE_SYRIATEL_NUMBERS

    async def edit_usdt_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit USDT wallets."""
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("🚫 ليس لديك صلاحيات المسؤول")
            return ConversationHandler.END

        context.user_data['editing_env_var'] = 'usdt'

        if update.message:
            await update.message.reply_text(
                "💰 أرسل محافظ USDT الجديدة (بالترتيب: Coinex, CWallet, Payeer, PEB20)",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 إلغاء", callback_data="admin_settings")
                ]])
            )
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.message.edit_text(
                "💰 أرسل محافظ USDT الجديدة (بالترتيب: Coinex, CWallet, Payeer, PEB20)",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 إلغاء", callback_data="admin_settings")
                ]])
            )
        return HANDLE_USDT_WALLETS