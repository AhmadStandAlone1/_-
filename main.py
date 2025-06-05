import logging
import os
import sys  # Import the sys module
from datetime import timedelta, datetime
import sqlite3
import json  # استيراد json
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# Add the directory containing product_handlers.py to the Python module search path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import local modules
from database import init_db, init_wal
from handlers import (
    start_command,
    help_command,
    cancel_command,
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
    back_to_main_callback,
    cancel_callback,
    handle_env_value,
    is_admin,
)
from admin_panel import AdminPanel
from recharge_manager import RechargeManager
from purchase_manager import PurchaseManager
# from products import GAME_PRODUCTS, APP_PRODUCTS # تم التعليق لأننا سنقوم بتحميلها من JSON
from keyboards import Keyboards
from log_manager import LogManager
from config import Config
from admin_handlers import (
    ADMIN_BAN_USER,
    ADMIN_UNBAN_USER,
    ADMIN_MODIFY_BALANCE,
    ban_user_callback,
    unban_user_callback,
    modify_balance_callback,
    edit_rate_callback,
    handle_rate_update,
    handle_user_input,
)
from purchase_handlers import (
    buy_callback,
    handle_game_id,
    cancel_purchase_callback
)
from product_handlers import (
    shop_callback,
    games_callback,
    apps_callback,
    game_packages_callback,
    app_packages_callback,
    handle_price_update,
    show_balance,  # Import the function
    show_orders,   # Import the function
)
from recharge_handlers import (
    charge_callback,
    crypto_payment_callback,
    syriatel_payment_callback,
    handle_amount,
    handle_txid,
    handle_photo
)
from edit_products_handlers import (
    edit_prices_callback,
    edit_games_callback,
    edit_apps_callback,
    edit_product_callback,
)

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Config
config = Config()

# Constants
BOT_TOKEN = config.BOT_TOKEN
SUPPORT_USERNAME = config.SUPPORT_USERNAME
OWNER_ID = config.OWNER_ID

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='diamond_store.log'
)
logger = logging.getLogger(__name__)

# Global variables to store products
GAME_PRODUCTS = {}
APP_PRODUCTS = {}


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generic error handler."""
    try:
        error_text = f"⚠️ خطأ في البوت: {str(context.error)}"
        logger.error(error_text)

        # Try sending a message to the user
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ عذراً، حدث خطأ غير متوقع\n"
                    "🔄 يرجى المحاولة مرة أخرى"
                )
            except Exception as e:
                logger.error(f"Could not send error message to user: {e}")

        # Send error details to the admin
        admin_text = (
            "⚠️ تنبيه: حدث خطأ في البوت\n\n"
            f"الخطأ: {str(context.error)}\n"
            f"المستخدم: {update.effective_user.id if update and update.effective_user else 'غير معروف'}\n"
            f"نوع التحديث: {update.update_id if update and update.effective_user else 'غير معروف'}\n"
            f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=admin_text
            )
        except Exception as e:
            logger.error(f"Could not send error message to admin: {e}")

    except Exception as e:
        logger.error(f"Error in error handler: {e}")


def load_products():
    """Load products from the products.json file."""
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            global GAME_PRODUCTS, APP_PRODUCTS
            GAME_PRODUCTS = data.get('games', {})
            APP_PRODUCTS = data.get('apps', {})
    except Exception as e:
        logger.error(f"Error loading products: {e}")


async def cleanup_expired_transactions(context: ContextTypes.DEFAULT_TYPE):
    """Clean up expired transactions."""
    conn = None
    try:
        conn = sqlite3.connect("diamond_store.db")
        c = conn.cursor()

        # Calculate the expiry time (e.g., 24 hours ago)
        expiry_time = datetime.now() - timedelta(hours=24)
        expiry_time_str = expiry_time.isoformat()

        # Fetch expired transaction IDs
        c.execute("SELECT tx_id FROM transactions WHERE status = 'pending' AND created_at < ?", (expiry_time_str,))
        expired_transactions = c.fetchall()

        if expired_transactions:
            logger.info(f"Found {len(expired_transactions)} expired transactions. Processing...")
            for (tx_id,) in expired_transactions:
                try:
                    # Update the transaction status to 'expired'
                    c.execute("UPDATE transactions SET status = 'expired' WHERE tx_id = ?", (tx_id,))
                    logger.info(f"Transaction {tx_id} marked as expired.")

                    # Log the action
                    logger.info(f"Expired transaction {tx_id} cleanup completed.")
                except sqlite3.Error as e:
                    logger.error(f"Error processing expired transaction {tx_id}: {e}")
                    conn.rollback()

            conn.commit()
            logger.info("Expired transactions cleanup completed successfully.")
        else:
            logger.info("No expired transactions found.")
    except sqlite3.Error as e:
        logger.error(f"Database error during cleanup: {e}")
    finally:
        if conn:
            conn.close()


def main():
    """Main function to run the bot."""
    try:
        # Bot token validation
        if not BOT_TOKEN:
            raise ValueError("❌ لم يتم العثور على توكن البوت في ملف .env")

        # Database initialization
        init_db()
        init_wal()
        load_products()

        # Application builder
        application = (
            Application.builder()
                .token(BOT_TOKEN)
                .concurrent_updates(True)
                .build()
        )

        # Initialize local modules
        admin_panel = AdminPanel()
        recharge_manager = RechargeManager()
        purchase_manager = PurchaseManager(GAME_PRODUCTS, APP_PRODUCTS)
        log_manager = LogManager()

        # Define conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(admin_panel.admin_panel, pattern=r"^admin_panel$"),
                CallbackQueryHandler(ban_user_callback, pattern=r"^ban_user$"),
                CallbackQueryHandler(unban_user_callback, pattern=r"^unban_user$"),
                CallbackQueryHandler(modify_balance_callback, pattern=r"^modify_balance$"),
                CallbackQueryHandler(edit_rate_callback, pattern=r"^edit_rate_[a-zA-Z]+$"),
                CallbackQueryHandler(admin_panel.admin_settings, pattern=r"^admin_settings$"),
                CallbackQueryHandler(admin_panel.edit_env_settings, pattern=r"^edit_env$"),
                CallbackQueryHandler(admin_panel.edit_syriatel_numbers, pattern=r"^edit_syriatel_numbers$"),
                CallbackQueryHandler(admin_panel.edit_usdt_wallets, pattern=r"^edit_usdt_wallets$"),
                CallbackQueryHandler(crypto_payment_callback, pattern=r"^pay_crypto_[a-zA-Z0-9_]+$"),
                CallbackQueryHandler(syriatel_payment_callback, pattern=r"^pay_syriatel$"),
                CallbackQueryHandler(buy_callback, pattern=r"^buy_(game|app)_[^_]+_[^_]+_[0-9]+$"),
                CallbackQueryHandler(edit_prices_callback, pattern=r"^edit_prices$"),
                CallbackQueryHandler(edit_games_callback, pattern=r"^edit_games$"),
                CallbackQueryHandler(edit_apps_callback, pattern=r"^edit_apps$"),
                CallbackQueryHandler(edit_product_callback, pattern=r"^edit_(game|app)_[^_]+$"),
                CallbackQueryHandler(shop_callback, pattern=r"^shop$"),  # Keep shop_callback here
                CallbackQueryHandler(recharge_manager.confirm_payment, pattern=r"^confirm_payment_"),
                CallbackQueryHandler(recharge_manager.reject_payment, pattern=r"^reject_payment_")
            ],
            states={
                ADMIN_BAN_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                ADMIN_UNBAN_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                ADMIN_MODIFY_BALANCE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                WAITING_FOR_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                WAITING_FOR_PAYMENT_PROOF: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_photo),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                WAITING_FOR_TXID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_txid),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                WAITING_FOR_GAME_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_id),
                ],
                WAITING_FOR_RATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rate_update),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                WAITING_FOR_PRICE_UPDATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_update),
                    CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                    CallbackQueryHandler(games_callback, pattern=r"^games$"),
                ],
                EDITING_ENV_VALUE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_env_value),
                ],
                HANDLE_SYRIATEL_NUMBERS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_env_value),
                ],
                HANDLE_USDT_WALLETS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_env_value),
                ],
                WAITING_FOR_REJECT_REASON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, recharge_manager.handle_reject_reason),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
                CallbackQueryHandler(shop_callback, pattern=r"^shop$"),
                CallbackQueryHandler(games_callback, pattern=r"^games$"),
                CallbackQueryHandler(cancel_callback, pattern=r"^cancel_reject$"),
                CallbackQueryHandler(back_to_main_callback, pattern=r"^back_to_main$"),
            ],
            per_message=False,
            per_chat=True,
            per_user=True,
            allow_reentry=True,
            name="diamond_store_bot"
        )

        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(conv_handler)  # Add the conversation handler
        application.add_handler(CallbackQueryHandler(show_balance, pattern=r"^my_balance$"))
        application.add_handler(CallbackQueryHandler(show_orders, pattern=r"^my_orders$"))
        application.add_handler(CallbackQueryHandler(shop_callback, pattern=r"^shop$"))
        application.add_handler(CallbackQueryHandler(games_callback, pattern=r"^games$"))
        application.add_handler(CallbackQueryHandler(apps_callback, pattern=r"^apps$"))
        application.add_handler(CallbackQueryHandler(game_packages_callback, pattern=r"^game_"))
        application.add_handler(CallbackQueryHandler(app_packages_callback, pattern=r"^app_"))
        application.add_handler(CallbackQueryHandler(charge_callback, pattern=r"^charge$"))

        # Add handlers for recharge_manager and purchase_manager using CallbackQueryHandler
        #application.add_handler(CallbackQueryHandler(recharge_manager.confirm_payment, pattern=r"^confirm_payment_"))
        #application.add_handler(CallbackQueryHandler(recharge_manager.reject_payment, pattern=r"^reject_payment_"))
        application.add_handler(CallbackQueryHandler(purchase_manager.accept_order, pattern=r"^complete_order_"))
        application.add_handler(CallbackQueryHandler(purchase_manager.reject_order, pattern=r"^cancel_order_"))

        application.add_handler(CallbackQueryHandler(back_to_main_callback, pattern=r"^back_to_main$"))

        application.add_handler(CommandHandler("admin", admin_panel.admin_panel))

        application.add_error_handler(error_handler)

        # Periodic tasks
        job_queue = application.job_queue
        job_queue.run_repeating(
            cleanup_expired_transactions,
            interval=timedelta(hours=1)
        )

        # Bot start info
        print("\n" + "=" * 50)
        print("✅ تم تشغيل البوت بنجاح")
        print(f"⏰ تاريخ التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 المطور: @{SUPPORT_USERNAME}")
        print(f"🤖 معرف البوت: @{os.getenv('BOT_USERNAME', 'diamond_store_sy_bot')}")
        print(f"📊 النسخة: 1.0")
        print("=" * 50 + "\n")

        # Run the bot
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    except Exception as e:
        logger.error(f"Critical error: {e}")
        print(f"❌ خطأ غير متوقع: {e}")
        print("\nتفاصيل الخطأ:")
        import traceback
        print(traceback.format_exc())
    finally:
        print("\n⚠️ تم إيقاف البوت")


if __name__ == "__main__":
    main()