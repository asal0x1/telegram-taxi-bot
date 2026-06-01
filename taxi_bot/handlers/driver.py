from transformers import Idefics3ImageProcessorFast

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
COMPLETED = 'COMPLETED'

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

    orders = db.get_pending_orders()
    if orders:
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
            )

        return ASSIGN
    else:
        update.message.reply_text(" hozirda buyurtmalar yo'q"
                                  )


def assaign_drivers(update, context):
    driver_id = update.effective_user.id
    order_id = update.message.text

    context.user_data['order_id'] = order_id

    db.assign_driver(driver_id, order_id)

    order = db.get_order(order_id)
    user_id = order['user_id']
    user = db.get_user(user_id)
    user_name = user['name']
    user_phone = user['phone']

    frm = coords_address(order[4], order[5])
    to = order[6]
    tariff = get_tariff_name(order[3])
    dist = order[7]
    price = order[8]
    formatted_price = f"{price:,}".replace(",", " ")

    update.message.reply_text(
        f"✅ Siz {order_id} sonidagi buyurtmani qabul qildingiz.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Mijoz: {user_name}\n"
        f"📞 Telefon: {user_phone}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Qayerdan: {frm}\n"
        f"🏁 Qayerga: {to}\n\n"
        f"📏 Masofa: {dist} km\n"
        f"💰 Yo'l haqi: {formatted_price} so'm\n"
        f"📦 Tarif: {tariff}\n"
    )

    notify_user(update, context, user_id, driver_id)
    return completed_b(update, context)

def completed_b(update, context):
    chat_id = update.effective_chat.id
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("Safarni yakunlash")]],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat_id,
                             reply_markup=reply_markup,
                             text= "Mijozni oborgandan so'ng shu tugmani bosing"
                             )
    return COMPLETED

def completed(update, context):
    chat_id = update.effective_user.id
    text = update.message.text
    order_id = context.user_data.get('order_id')

    if text == "Safarni yakunlash":
        update.message.reply_text(
            "🏁 Safar yakunlandi!\n\n"
            "✅ Buyurtma muvaffaqiyatli yopildi.\n"
            "🚖 Yangi buyurtmalarni qabul qilishga tayyorsiz.\n\n"
            "🙏 Hamkorligingiz uchun rahmat!")
        db.delete_order(order_id)
        return choose_order(update, context)

def notify_user(update, context, user_id, driver_id):
    from handlers.user import main_menu
    driver = db.get_driver(driver_id)

    driver_name = driver['name']
    phone = driver['phone']
    car_model = driver['car_model']
    car_number = driver['car_number']

    context.bot.send_message(
        chat_id=user_id,
        text =
        " 🎉 Buyurtmangiz qabul qilindi!\n\n"
        "🚖 Haydovchi yo'lga chiqishga tayyor.\n\n"
        "👨‍✈️ Haydovchi ma'lumotlari:\n"
        f"👤 {driver_name}\n"
        f"📞 {phone}\n"
        f"🚗 {car_model}\n"
        f"🔢 {car_number}\n\n"
        "📱 Zarurat bo'lsa, haydovchi siz bilan bog'lanadi.\n\n"
        "🙏 Bizni tanlaganingiz uchun rahmat!\n"
        "😊 Yoqimli va xavfsiz safar tilaymiz!"
        )

    return main_menu(update, context)










