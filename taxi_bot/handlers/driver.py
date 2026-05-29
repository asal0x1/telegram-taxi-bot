import db
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup
from handlers.user import *
from utils import *

MODEL = 'DRIVER_MODEL'
NUMBER = 'DRIVER_NUMBER'
D_TARIFF = 'DRIVER_TARIFF'
LOCATION = 'LOCATION'
ASSIGN = 'ASSIGN'

def car_model(update, context):
    context.user_data['car_model'] = update.message.text
    update.message.reply_text("What is your car number")
    return NUMBER


def car_number(update, context):
    context.user_data['car_number'] = update.message.text
    reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Start", callback_data='tariff_1')],
                [InlineKeyboardButton("Comfort", callback_data='tariff_2')],
                [InlineKeyboardButton("Biznes", callback_data='tariff_3')]
        ])
    update.message.reply_text("O'zingiz ishlaydigan tarifni tanlang:",
                              reply_markup=reply_markup)
    return D_TARIFF

def tariff_callback_d(update, context):
    query = update.callback_query
    query.answer()
    tariff_id = int(query.data.split('_')[1])
    context.user_data['tariff_id'] = tariff_id

    db.add_driver(
        update.effective_user.id,
        context.user_data['tariff_id'] ,
        context.user_data['name'],
        context.user_data['phone'],
        context.user_data['car_model'],
        context.user_data['car_number'],
        )

    query.message.reply_text("Ro'yxatdan muvaffaqiyatli o'tdingiz! ✅")
    return choose_order(update, context)

def choose_order(update, context):
    msg = update.message if update.message else update.callback_query.message

    orders = db.get_orders()
    for order in orders:
        order_id = order[0]
        frm = coords_address(order[4], order[5])
        to = order[6]
        tariff = get_tariff_name(order[3])
        dist = order[7]
        price = order[8]
        formatted_price = f"{price:,}".replace(",", " ")

        msg.reply_text(f"🚖 **YANGI BUYURTMA! [ID: {order_id}]**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **Qayerdan:** {frm}\n"
        f"🏁 **Qayerga:** {to}\n\n"
        f"📏 **Masofa:** {dist} km\n"
        f"💰 **Yo'l haqi:** {formatted_price} so'm\n"
        f"📦 **Tarif:** {tariff}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✍️ *Buyurtmani qabul qilish uchun quyida uning ID raqamini ({order_id}) kiriting:* ")

    return ASSIGN

def assaign_drivers(update, context):
    driver_id = update.effective_user.id
    order_id = update.message.text
    db.assign_driver(driver_id, order_id)
    update.message.reply_text(f"Siz {order_id} sonidagi buyurtmani qabul qildingiz. ")











