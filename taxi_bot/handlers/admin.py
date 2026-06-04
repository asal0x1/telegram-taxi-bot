from config import ADMIN_PASSWORD
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import CallbackContext
import db

ADMIN = set()

# --- States ---
ADMIN_MENU         = 'ADMIN_MENU'
ADMIN_PASSWORD_ST  = 'ADMIN_PASSWORD'
ADMIN_TARIFF_NAME  = 'ADMIN_TARIFF_NAME'
ADMIN_TARIFF_BASE  = 'ADMIN_TARIFF_BASE'
ADMIN_TARIFF_KM    = 'ADMIN_TARIFF_KM'
ADMIN_TARIFF_EDIT  = 'ADMIN_TARIFF_EDIT'
ADMIN_EDIT_FIELD   = 'ADMIN_EDIT_FIELD'
ADMIN_EDIT_VALUE   = 'ADMIN_EDIT_VALUE'

# ──────────────────────────────────────────
# Keyboards
# ──────────────────────────────────────────

def admin_main_keyboard():
    keyboard = [
        [KeyboardButton("📋 Buyurtmalar"),   KeyboardButton("🚗 Haydovchilar")],
        [KeyboardButton("📊 Statistika")],
        [KeyboardButton("🚪 Chiqish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ──────────────────────────────────────────
# Login / Logout
# ──────────────────────────────────────────

def admin_login(update: Update, context: CallbackContext):
    update.message.reply_text("🔐 Admin parolini kiriting:")
    return ADMIN_PASSWORD_ST


def check_admin_password(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    if update.message.text == ADMIN_PASSWORD:
        ADMIN.add(chat_id)
        update.message.reply_text(
            "✅ Admin paneliga xush kelibsiz!",
            reply_markup=admin_main_keyboard()
        )
        return ADMIN_MENU
    else:
        update.message.reply_text("❌ Parol noto'g'ri. Qayta urinib ko'ring:")
        return ADMIN_PASSWORD_ST


def admin_logout(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    ADMIN.discard(chat_id)
    update.message.reply_text("🚪 Admin paneldan chiqdingiz.")
    # Foydalanuvchi asosiy start ga qaytadi
    from handlers.user import start
    return start(update, context)


def is_admin(chat_id: int) -> bool:
    return chat_id in ADMIN


# ──────────────────────────────────────────
# Admin menu dispatcher
# ──────────────────────────────────────────

def admin_menu_select(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "📋 Buyurtmalar":
        return admin_orders(update, context)
    elif text == "🚗 Haydovchilar":
        return admin_drivers(update, context)

    elif text == "📊 Statistika":
        return admin_stats(update, context)

    elif text == "🚪 Chiqish":
        return admin_logout(update, context)
    else:
        update.message.reply_text("❓ Noma'lum buyruq.")
        return ADMIN_MENU


# ──────────────────────────────────────────
# 1. Buyurtmalarni boshqarish
# ──────────────────────────────────────────

def admin_orders(update: Update, context: CallbackContext):
    orders = db.get_orders()
    if not orders:
        update.message.reply_text("📋 Hozirda buyurtmalar yo'q.")
        return ADMIN_MENU

    for order in orders:
        order_id   = order['order_id']
        user_id    = order['user_id']
        driver_id  = order['driver_id']
        status     = order['status']
        to_loc     = order['to_location']
        dist       = order['distance_km']
        price      = order['total_price']
        created_at = order['created_at']

        formatted_price = f"{price:,}".replace(",", " ")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🗑 O'chirish",
                callback_data=f"admin_del_order_{order_id}"
            )]
        ])

        update.message.reply_text(
            f"🆔 Buyurtma: #{order_id}\n"
            f"👤 Foydalanuvchi: {user_id}\n"
            f"🚗 Haydovchi: {driver_id}\n"
            f"📍 Qayerga: {to_loc}\n"
            f"📏 Masofa: {dist} km\n"
            f"💰 Narx: {formatted_price} so'm\n"
            f"📌 Holat: {status}\n"
            f"📅 Sana: {created_at}",
            reply_markup=keyboard
        )

    return ADMIN_MENU


def admin_delete_order_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    order_id = int(query.data.split("_")[-1])
    db.delete_order(order_id)
    query.message.edit_text(f"✅ #{order_id} buyurtma o'chirildi.")
    return ADMIN_MENU


# ──────────────────────────────────────────
# 2. Haydovchilarni boshqarish
# ──────────────────────────────────────────

def admin_drivers(update: Update, context: CallbackContext):
    drivers = db.get_drivers()
    if not drivers:
        update.message.reply_text("🚗 Haydovchilar ro'yxati bo'sh.")
        return ADMIN_MENU

    for driver in drivers:
        driver_id  = driver['driver_id']
        name       = driver['name' ]
        phone      = driver['phone' ]
        car_model  = driver['car_model' ]
        car_number = driver['car_number' ]
        tariff_id  = driver['tariff_id' ]



        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🗑 O'chirish",  callback_data=f"admin_del_driver_{driver_id}"),
            ]
        ])

        update.message.reply_text(
            f" Haydovchi: {name}\n"
            f"📞 Telefon: {phone}\n"
            f"🚗 Mashina: {car_model} | {car_number}\n"
            f"📦 Tarif ID: {tariff_id}\n"
            f"🆔 Telegram ID: {driver_id}",
            reply_markup=keyboard
        )

    return ADMIN_MENU



# ──────────────────────────────────────────
# 3. Tariflarni boshqarish
# ──────────────────────────────────────────

def admin_tariffs_menu(update: Update, context: CallbackContext):
    tariffs = db.get_tariffs()

    keyboard = [[InlineKeyboardButton("➕ Yangi tarif qo'shish", callback_data="admin_add_tariff")]]

    if tariffs:
        for t in tariffs:
            keyboard.append([
                InlineKeyboardButton(
                    f"✏️ {t['name']}",
                    callback_data=f"admin_edit_tariff_{t['id']}"
                ),
                InlineKeyboardButton(
                    "🗑",
                    callback_data=f"admin_del_tariff_{t['id']}"
                )
            ])

    update.message.reply_text(
        "💰 Tariflar boshqaruvi:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADMIN_MENU


def admin_add_tariff_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['admin_action'] = 'add_tariff'
    query.message.reply_text("Yangi tarif nomini kiriting (masalan: Start, Comfort, Business):")
    return ADMIN_TARIFF_NAME


def admin_tariff_name(update: Update, context: CallbackContext):
    context.user_data['new_tariff_name'] = update.message.text.strip()
    update.message.reply_text("Boshlang'ich narxni kiriting (so'mda):")
    return ADMIN_TARIFF_BASE


def admin_tariff_base(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text.isdigit():
        update.message.reply_text("❌ Faqat raqam kiriting:")
        return ADMIN_TARIFF_BASE
    context.user_data['new_tariff_base'] = int(text)
    update.message.reply_text("1 km uchun narxni kiriting (so'mda):")
    return ADMIN_TARIFF_KM



def admin_tariff_field_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    parts    = query.data.split("_")  # admin_tariff_field_<field>_<id>
    field    = parts[3]
    tariff_id = int(parts[4])

    context.user_data['edit_tariff_id']    = tariff_id
    context.user_data['edit_tariff_field'] = field

    labels = {"name": "nom", "base": "boshlang'ich narx (so'm)", "km": "km narxi (so'm)"}
    query.message.reply_text(f"Yangi {labels.get(field, field)} kiriting:")
    return ADMIN_EDIT_VALUE




# ──────────────────────────────────────────
# 4. Statistika
# ──────────────────────────────────────────

def admin_stats(update: Update, context: CallbackContext):
    stats = db.get_stats()

    total_orders     = stats.get('total_orders', 0)
    completed_orders = stats.get('completed_orders', 0)
    pending_orders   = stats.get('pending_orders', 0)
    total_drivers    = stats.get('total_drivers', 0)

    total_users      = stats.get('total_users', 0)


    update.message.reply_text(
        "📊 *Bot statistikasi*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Jami buyurtmalar:      {total_orders}\n"
        f"✅ Yakunlangan:           {completed_orders}\n"
        f"⏳ Kutilayotgan:          {pending_orders}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🚗 Jami haydovchilar:     {total_drivers}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Jami foydalanuvchilar: {total_users}\n",
        parse_mode="Markdown"
    )
    return ADMIN_MENU


# ──────────────────────────────────────────
# Callback router  (ConversationHandler'da
# CallbackQueryHandler uchun)
# ──────────────────────────────────────────

