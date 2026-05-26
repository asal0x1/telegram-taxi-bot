from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CallbackQueryHandler, PreCheckoutQueryHandler

import db
from config import *
from db import get_user_orders
from handlers.driver import *
from keyboards import *
from utils import *


user_language = {}


NAME = 'USER_NAME'
PHONE = 'USER_PHONE'
LANGUAGE = 'USER_LANGUAGE'
WHO = 'USER_WHO'
MAIN_MENU = 'USER_MAIN_MENU'
FROM_LOCATION = 'USER_FROM_LOCATION'
TO_LOCATION = 'USER_TO_LOCATION'
TARIFF = 'USER_TARIFF'
SETTING = 'USER_SETTING'





def start(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id

    user = db.get_user(chat_id)
    driver = db.get_driver(chat_id)
    if user:
        user_language[chat_id] = user['language']

        return main_menu(update, context)
    if driver:
        return choose_order(update, context)


    update.message.reply_text("👤 Ism familyangizni kiriting: ")
    return NAME

def get_name(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    update.message.reply_text(
        "📞 Telefon raqamingizni yuboring",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Telefon yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return PHONE

def get_phone(update: Update, context: CallbackContext):
    context.user_data['phone'] = update.message.contact.phone_number
    buttons = LANG_BUTTONS.get(user_language.get(update.effective_user.id, "uz"))
    keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons]

    update.message.reply_text(
        "Tilni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return LANGUAGE

def get_language(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    chat_id = update.effective_user.id
    lang = query.data.split('_')[1]

    user = db.get_user(chat_id)

    if user:
        db.update_language(chat_id, lang)

        query.message.reply_text("Til muvaffaqiyatli o'zgartirildi ✅")

        return main_menu(update, context)

    else:
        keyboards = [
            [KeyboardButton("Passenger")],
            [KeyboardButton("Driver")],
        ]

        query.message.reply_text(
            "Выберите кем вы являетесь?",
            reply_markup=ReplyKeyboardMarkup(
                keyboards,
                resize_keyboard=True
            )
        )

        return WHO

def who(update: Update, context: CallbackContext):
    answer = update.message.text
    if answer == "Passenger":
        db.add_user(
            update.effective_user.id,
            context.user_data['name'],
            context.user_data['phone'],
            context.user_data['language'],
        )
        update.message.reply_text(get_text(update.effective_user.id, "Accepted"))
        return main_menu(update, context)
    elif answer == "Driver":

        update.message.reply_text(" What is your car model ")
        return MODEL



def main_menu(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")
    buttons = MENU_BUTTONS[lang]
    keyboard = [
        [KeyboardButton(buttons[0])],
        [KeyboardButton(buttons[1]), KeyboardButton(buttons[2])],
        [KeyboardButton(buttons[3]), KeyboardButton(buttons[4])],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    if update.message:
        update.message.reply_text(get_text(chat_id, "start"), reply_markup=reply_markup)
    else:
        update.callback_query.message.reply_text(get_text(chat_id, "start"), reply_markup=reply_markup)

    return MAIN_MENU




def get_from_location(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")

    location = update.message.location
    context.user_data['from_lat'] = location.latitude
    context.user_data['from_lon'] = location.longitude


    update.message.reply_text(
        TEXTS[lang]["to_location"]
    )
    return TO_LOCATION


def get_to_location(update: Update, context: CallbackContext):
    lang = user_language.get(update.effective_user.id, "uz")
    context.user_data['to_location'] = update.message.text


    update.message.reply_text(
        TEXTS[lang]["tariff"],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start", callback_data="tariff_1")],
            [InlineKeyboardButton("Comfort", callback_data="tariff_2")],
            [InlineKeyboardButton("Business", callback_data="tariff_3")]
    ])
    )
    return TARIFF

def tariff_callback(update, context):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")
    query = update.callback_query

    tariff_id = int(query.data.split('_')[1])

    query.answer()
    get_tariff_name(tariff_id)

    context.user_data['distance_km']  = 0  #
    context.user_data['total_price'] = 0  #
    context.user_data['status'] = "pending" #

    context.user_data['tariff_id'] = tariff_id
    db.create_order(
        chat_id,
        context.user_data['from_lat'],
        context.user_data['from_lon'],
        context.user_data['to_location'],
        context.user_data['tariff_id'],

        context.user_data['distance_km'], #
        context.user_data['total_price'] #
    )

    query.message.reply_text(
        TEXTS[lang]["feedback_received"]

    )
    return main_menu(update, context)


def get_text(chat_id, key):
    lang = user_language.get(chat_id, 'uz')
    return TEXTS[lang][key]

def order_taxi(update, context):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")

    update.message.reply_text(
        TEXTS[lang]["from_location"],
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(TEXTS[lang]["from_location"], request_location=True)]],
            resize_keyboard=True,
        )
    )
    return FROM_LOCATION

def my_orders(update, context):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")

    orders = get_user_orders(chat_id)

    if orders:
        text = "📜 Your Orders History:\n\n"

        for order in orders:
            text += (
                f"📍 To: {order['to_location']}\n"
                f"💰 Price: {order['total_price']}\n"
                f"📅 Date: {order['created_at']}\n\n"
            )

        update.message.reply_text(text)

    else:
        update.message.reply_text(
            TEXTS[lang]["no_orders"]
        )

    return MAIN_MENU

def my_tarrifs(update, context):
    pass


def my_help(update, context):
    pass





def my_setting(update, context):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")
    buttons = SETTING_BUTTONS[lang]
    keyboard = [
        [KeyboardButton(buttons[0])],
        [KeyboardButton(buttons[1]), KeyboardButton(buttons[2])],
        [KeyboardButton(buttons[3])],

    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(text="⚙️ Sozlamalar", reply_markup=reply_markup)


    return SETTING


def back(update, context):
    return main_menu(update, context)



def setting_select(update, context):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")
    buttons = SETTING_BUTTONS[lang]
    text = update.message.text

    if text == buttons[0]:
        return change_language(update, context)
    elif text == buttons[1]:
        return change_phone(update, context)
    elif text == buttons[2]:
        return change_name(update, context)
    elif text == buttons[3]:
        return back(update, context)

def change_phone(update, context):
    pass
def change_name(update, context):
    pass

def main_menu_select(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    lang = user_language.get(chat_id, "uz")
    buttons = MENU_BUTTONS[lang]
    text = update.message.text

    if text == buttons[0]:
        return order_taxi(update, context)
    elif text == buttons[1]:
        return my_orders(update, context)
    elif text == buttons[2]:
        return my_tarrifs(update, context)
    elif text == buttons[3]:
        return my_help(update, context)
    elif text == buttons[4]:
        return my_setting(update, context)



def change_language(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    buttons = LANG_BUTTONS.get(user_language.get(chat_id, "uz"))

    keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons]

    update.message.reply_text(
        "Tilni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return LANGUAGE



def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.effective_user.id

    lang = user_language.get(chat_id, "uz")
    buttons = MENU_BUTTONS[lang]

    if text == buttons[4]:
        buttons = LANG_BUTTONS[lang]
        keyboard = [
            [InlineKeyboardButton(text, callback_data=c)]
            for text, c in buttons
        ]

        update.message.reply_text(
            "Tilni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        change_language(update, context)
        return main_menu(update, context)
    elif text == buttons[3]:
        query = update.callback_query
        query.answer()
        query.message.reply_text("Hozirda yordam yoq")
        return main_menu(update, context)
    return None