import db
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup
from handlers.user import *

MODEL = 'DRIVER_MODEL'
NUMBER = 'DRIVER_NUMBER'
D_TARIFF = 'DRIVER_TARIFF'





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
    update.message.reply_text("here is orders ")
