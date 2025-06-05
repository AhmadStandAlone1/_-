import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

# Import local modules
from keyboards import Keyboards
from config import Config
import json

# Initialize Config
config = Config()

# Logger
logger = logging.getLogger(__name__)

async def edit_prices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the edit prices callback."""
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        "💰 اختر القسم:",
        reply_markup=Keyboards.edit_prices_menu()
    )
    return ConversationHandler.END

async def edit_games_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the edit games callback."""
    query = update.callback_query
    await query.answer()

    with open('products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        GAME_PRODUCTS = data.get('games', {})

    buttons = []
    for product_id, product in GAME_PRODUCTS.items():
        buttons.append([InlineKeyboardButton(f"{product['icon']} {product['name']}", callback_data=f"edit_game_{product_id}")])
    buttons.append([InlineKeyboardButton("➕ إضافة منتج", callback_data="add_game")])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="edit_prices")])

    await query.message.edit_text(
        "🎮 اختر اللعبة لتعديل أسعارها:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ConversationHandler.END

async def edit_apps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the edit apps callback."""
    query = update.callback_query
    await query.answer()

    with open('products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        APP_PRODUCTS = data.get('apps', {})

    buttons = []
    for product_id, product in APP_PRODUCTS.items():
        buttons.append([InlineKeyboardButton(f"{product['icon']} {product['name']}", callback_data=f"edit_app_{product_id}")])
    buttons.append([InlineKeyboardButton("➕ إضافة منتج", callback_data="add_app")])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="edit_prices")])

    await query.message.edit_text(
        "📱 اختر التطبيق لتعديل سعره:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ConversationHandler.END

async def edit_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the edit product callback."""
    query = update.callback_query
    await query.answer()

    product_type = query.data.split('_')[1]
    product_id = query.data.split('_')[2]

    with open('products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        GAME_PRODUCTS = data.get('games', {})
        APP_PRODUCTS = data.get('apps', {})

    if product_type == 'game':
        product = GAME_PRODUCTS[product_id]
        product_name = product['name']
    elif product_type == 'app':
        product = APP_PRODUCTS[product_id]
        product_name = product['name']
    else:
        await query.message.edit_text("❌ نوع المنتج غير صحيح")
        return ConversationHandler.END

    await query.message.edit_text(
        f"✏️ تعديل {product_name}\n\n"
        "أرسل السعر الجديد"
    )
    context.user_data['product_type'] = product_type
    context.user_data['product_id'] = product_id
    from handlers import WAITING_FOR_PRICE_UPDATE
    return WAITING_FOR_PRICE_UPDATE