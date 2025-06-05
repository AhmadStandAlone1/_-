from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class Keyboards:
    @staticmethod
    def main_menu(is_admin=False):
        """Main menu keyboard."""
        buttons = [
            [InlineKeyboardButton("💎 المتجر", callback_data="shop")],
            [InlineKeyboardButton("💰 شحن رصيد", callback_data="charge")],
            [InlineKeyboardButton("💳 رصيدي", callback_data="my_balance")],
            [InlineKeyboardButton("📦 طلباتي", callback_data="my_orders")]
        ]
        if is_admin:
            buttons.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def shop_menu():
        """Shop menu keyboard."""
        buttons = [
            [InlineKeyboardButton("🎮 الألعاب", callback_data="games")],
            [InlineKeyboardButton("📱 التطبيقات", callback_data="apps")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def payment_methods():
        """Payment methods keyboard."""
        from recharge_manager import PAYMENT_METHODS
        buttons = []

        # USDT buttons
        usdt_buttons = []
        for name, details in PAYMENT_METHODS['crypto']['options']:
            usdt_buttons.append(
                InlineKeyboardButton(f"💰 {name}", callback_data=f"pay_crypto_{name.lower()}")
            )

        # Arrange USDT buttons in rows of 2
        for i in range(0, len(usdt_buttons), 2):
            row = usdt_buttons[i:i+2]
            buttons.append(row)

        # Syriatel Cash button
        buttons.append([InlineKeyboardButton("📱 سيرياتيل كاش", callback_data="pay_syriatel")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def admin_panel():
        """Admin panel keyboard."""
        buttons = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [
                InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users"),
                InlineKeyboardButton("💰 تعديل الأسعار", callback_data="edit_prices")
            ],
            [
                InlineKeyboardButton("💳 طلبات الشحن", callback_data="admin_recharges"),
                InlineKeyboardButton("📦 الطلبات المعلقة", callback_data="admin_orders")
            ],
            [
                InlineKeyboardButton("⚙️ إعدادات عامة", callback_data="admin_settings"),
                InlineKeyboardButton("💱 أسعار الصرف", callback_data="admin_rates")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def manage_users_menu():
        """Manage users keyboard."""
        buttons = [
            [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user")],
            [InlineKeyboardButton("✅ إلغاء حظر مستخدم", callback_data="unban_user")],
            [InlineKeyboardButton("💰 تعديل رصيد", callback_data="modify_balance")],
            [InlineKeyboardButton("📊 عرض المستخدمين", callback_data="list_users")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def edit_prices_menu():
        """Edit prices keyboard."""
        buttons = [
            [
                InlineKeyboardButton("🎮 منتجات الألعاب", callback_data="edit_games"),
                InlineKeyboardButton("📱 منتجات التطبيقات", callback_data="edit_apps")
            ],
            [
                InlineKeyboardButton("➕ إضافة منتج", callback_data="add_product"),
                InlineKeyboardButton("❌ حذف منتج", callback_data="delete_product")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def admin_rates():
        """Admin rates keyboard."""
        buttons = [
            [InlineKeyboardButton("💵 سعر الدولار", callback_data="edit_rate_usd")],
            [InlineKeyboardButton("💰 سعر USDT", callback_data="edit_rate_usdt")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def confirm_cancel_order(order_id: int):
        """Confirm/cancel order buttons."""
        buttons = [
            [
                InlineKeyboardButton("✅ تأكيد", callback_data=f"complete_order_{order_id}"),
                InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_order_{order_id}")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_orders")]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def user_contact(user_id: int, username: str = None):
        """User contact button."""
        if username:
            return InlineKeyboardMarkup([[
                InlineKeyboardButton("💬 تواصل", url=f"https://t.me/{username}")
            ]])
        else:
            return InlineKeyboardMarkup([[
                InlineKeyboardButton("💬 تواصل", url=f"tg://user?id={user_id}")
            ]])