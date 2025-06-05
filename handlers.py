import logging
import sqlite3
import os
from datetime import datetime
from telegram import Update, ChatMember
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from config import get_config
import sys
from keyboards import Keyboards
from utils import format_currency

# Initialize Config
config = get_config()

# Constants
OWNER_ID = config.OWNER_ID
FORCED_CHANNEL_ID = config.FORCED_CHANNEL_ID
FORCED_CHANNEL_USERNAME = config.FORCED_CHANNEL_USERNAME
SUPPORT_USERNAME = config.SUPPORT_USERNAME
DB_PATH = "diamond_store.db"

# States for ConversationHandler
(
    ADMIN_BAN_USER,
    ADMIN_UNBAN_USER,
    ADMIN_MODIFY_BALANCE,
    WAITING_FOR_AMOUNT,
    WAITING_FOR_PAYMENT_PROOF,
    WAITING_FOR_TXID,
    WAITING_FOR_RATE,
    WAITING_FOR_GAME_ID,
    WAITING_FOR_USER_INPUT,
    WAITING_FOR_EMAIL,
    WAITING_FOR_OPERATION_ID,
    WAITING_FOR_PRICE_UPDATE,
    WAITING_FOR_REJECT_REASON,
    WAITING_FOR_PRODUCT_INFO,
    EDITING_ENV_VALUE,
    HANDLE_SYRIATEL_NUMBERS,
    HANDLE_USDT_WALLETS,
) = range(17)

# Logger
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user = update.effective_user

    if not await check_subscription(user.id, context.bot):
        channel_link = f"https://t.me/{FORCED_CHANNEL_USERNAME}"
        await update.message.reply_text(
            f"🔒 عذراً {user.first_name}،\n"
            f"يجب عليك الاشتراك في قناتنا أولاً:\n"
            f"{channel_link}\n\n"
            "بعد الاشتراك، أرسل /start مرة أخرى 🔄"
        )
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now()
        c.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, username, first_name, joined_date, last_activity)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.first_name, now, now))
        conn.commit()

        welcome_text = (
            f"👋 مرحباً {user.first_name}\n\n"
            "💎 أهلاً بك في متجر الدايموند\n"
            "🏪 نقدم أفضل الأسعار وخدمة فورية\n\n"
            "📢 عروض اليوم:\n"
            "• شحن PUBG بأفضل الأسعار 🔫\n"
            "• كود شحن مباشر من الموقع الرسمي 🎮\n"
            "• شحن Free Fire بأرخص الأسعار 🔥\n"
            "• خصومات على جميع التطبيقات 📱\n\n"
            "💳 طرق الدفع المتاحة:\n"
            "• USDT (Coinex/CWallet/PEB20) 💰\n"
            "• USD (PAYEER) 💰\n"
            "• سيرياتيل كاش 📱\n\n"
            "💱 أسعار الصرف:\n"
            f"• الدولار: {format_currency(float(config.USD_RATE))}\n"
            f"• USDT: {format_currency(float(config.USDT_RATE))}\n\n"
            "اختر من القائمة:"
        )
        await update.message.reply_text(
            welcome_text,
            reply_markup=Keyboards.main_menu(is_admin(user.id))
        )

    except sqlite3.Error as e:
        logger.error(f"Database error in start_command: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقًا."
        )
    finally:
        if conn:
            conn.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    help_text = (
        "💎 مرحباً بك في متجر الدايموند\n\n"
        "📝 الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/help - عرض هذه المساعدة\n"
        "/cancel - إلغاء العملية الحالية\n\n"
        "👋 للبدء، اضغط على الأزرار في القائمة الرئيسية\n\n"
        f"💬 للدعم الفني تواصل مع: @{SUPPORT_USERNAME}"
    )
    await update.message.reply_text(help_text)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /cancel command."""
    context.user_data.clear()
    await update.message.reply_text(
        "✅ تم إلغاء العملية الحالية\n"
        "يمكنك بدء عملية جديدة",
        reply_markup=Keyboards.main_menu(is_admin(update.effective_user.id))
    )
    return ConversationHandler.END

async def check_subscription(user_id: int, bot) -> bool:
    """Check if the user is subscribed to the required channel."""
    try:
        member = await bot.get_chat_member(FORCED_CHANNEL_ID, user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

def load_products():
    """Load products from the products.json file."""
    try:
        import json
        if os.path.exists('products.json'):
            with open('products.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                global GAME_PRODUCTS, APP_PRODUCTS
                GAME_PRODUCTS = data.get('games', GAME_PRODUCTS)
                APP_PRODUCTS = data.get('apps', APP_PRODUCTS)
    except Exception as e:
        logger.error(f"Error loading products: {e}")

async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "اختر من القائمة:",
        reply_markup=Keyboards.main_menu(is_admin(query.from_user.id))
    )
    return ConversationHandler.END

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "تم الإلغاء",
        reply_markup=Keyboards.main_menu(is_admin(query.from_user.id))
    )
    return ConversationHandler.END

async def handle_env_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input for editing .env variables."""
    user_input = update.message.text.strip()
    editing_var = context.user_data.get('editing_env_var')

    from admin_panel import AdminPanel # Import here to avoid circular dependencies
    admin_panel = AdminPanel()

    if editing_var == 'syriatel':
        syriatel_numbers = [num.strip() for num in user_input.split(',')]
        from config import Config # Import here to avoid circular dependencies
        config = get_config()
        success = config.update_syriatel_numbers(syriatel_numbers)

        if success:
            await update.message.reply_text(
                "✅ تم تحديث أرقام سيرياتيل كاش بنجاح",
                reply_markup=Keyboards.main_menu(is_admin(update.effective_user.id))
            )
        else:
            await update.message.reply_text(
                "❌ حدث خطأ أثناء تحديث أرقام سيرياتيل كاش",
                reply_markup=Keyboards.main_menu(is_admin(update.effective_user.id))
            )

    elif editing_var == 'usdt':
        usdt_wallets = [wallet.strip() for wallet in user_input.split(',')]
          # Ensure we have exactly 4 wallets
        if len(usdt_wallets) != 4:
            await update.message.reply_text(
                "❌ يجب إدخال 4 محافظ USDT بالترتيب: Coinex, CWallet, Payeer, PEB20",
                reply_markup=Keyboards.main_menu(is_admin(update.effective_user.id))
            )
            return ConversationHandler.END
        from config import Config # Import here to avoid circular dependencies
        config = get_config()

        success = config.update_usdt_wallets({
            "coinex": usdt_wallets[0],
            "cwallet": usdt_wallets[1],
            "payeer": usdt_wallets[2],
            "peb20": usdt_wallets[3],
        })

        if success:
            await update.message.reply_text(
                "✅ تم تحديث محافظ USDT بنجاح",
                reply_markup=Keyboards.main_menu(is_admin(update.effective_user.id))
            )
        else:
            await update.message.reply_text(
                "❌ حدث خطأ أثناء تحديث محافظ USDT",
                reply_markup=Keyboards.main_menu(is_admin(update.effective_user.id))
            )

    else:
        await update.message.reply_text(
            "❌ لم يتم تحديد متغير .env للتعديل",
            reply_markup=Keyboards.main_menu(is_admin(update.effective_user.id))
        )

    return ConversationHandler.END

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    ADMINS = [int(x) for x in os.getenv('ADMINS', str(OWNER_ID)).split(',')]
    return user_id in ADMINS


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restarts the bot."""
    config = get_config()
    user_id = update.message.from_user.id
    if user_id in config.ADMINS:
        await update.message.reply_text("جاري إعادة تشغيل البوت...")
        # Properly disconnect the bot
        await context.application.shutdown()
        # Restart the process
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        await update.message.reply_text("ليس لديك صلاحية لتنفيذ هذا الأمر.")