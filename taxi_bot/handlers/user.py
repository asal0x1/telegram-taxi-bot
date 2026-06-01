from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, \
    ConversationHandler, CallbackQueryHandler, PreCheckoutQueryHandler

import db
from config import *
from db import get_user_orders
from geocoder_coords import coords_address, address_to_coords
from handlers.driver import *
from keyboards import *
from utils import *
from utils import get_tariff_name
import math

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
CANCEL = 'USER_CANCEL'



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
        context.user_data['language'] = lang
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
    context.user_data['from_lat'] = float(update.message.location.latitude)
    context.user_data['from_lon'] = float(update.message.location.longitude)


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

    query.answer()
    tariff_id = int(query.data.split('_')[1])
    get_tariff_name(tariff_id)

    context.user_data['status'] = "pending" #
    context.user_data['tariff_id'] = tariff_id

    return price_way(tariff_id, update, context)

def get_distance(longitude_start, latitude_start, longitude_end, latitude_end):
    x1 = float(longitude_start)
    y1 = float(latitude_start)
    x2 = float(longitude_end)
    y2 = float(latitude_end)

    y= math.radians((y2+y1) / 2)
    x = math.cos(y)
    n = abs(x1 - x2) * 111000 * x
    n2 = abs(y1 - y2) * 111000
    length_way = round(math.sqrt(n * n + n2 * n2))

    return length_way
    # mumiy narx = boshlang‘ich narx + masofa narxi + qo‘shimcha xizmatla
def price_way(tariff_id, update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    tariff = db.get_tariff(tariff_id)
    to_there = address_to_coords( context.user_data['to_location'] )
    dist = get_distance(context.user_data['from_lon'], context.user_data['from_lat'],
                        float(to_there[0]), float(to_there[1]))
    dist_km = round(dist/1000, 2)
    total_price = tariff['base_price'] + (tariff['price_per_km'] * dist_km)
    context.user_data['total_price'] = round(total_price)

    print(total_price)
    print(context.user_data['total_price'])
    context.user_data['distance_km'] = dist_km
    print(context.user_data['distance_km'])
    # Tekshiring:
    print(context.user_data['from_lon'])  # qancha?
    print(context.user_data['from_lat'])  # qancha?
    print(to_there)  # address_to_coords nima qaytaradi?

    order_id = db.create_order(
        chat_id,
        context.user_data['from_lat'],
        context.user_data['from_lon'],
        context.user_data['to_location'],
        context.user_data['tariff_id'],

        context.user_data['distance_km'], #
        context.user_data['total_price'] #
    )
    context.user_data['order_id'] = order_id
    from_here = coords_address(context.user_data['from_lon'], context.user_data['from_lat']
                               )
    formatted_price = f"{context.user_data['total_price']:,}".replace(",", " ")

    update.callback_query.message.reply_text(
        f"Sizning {from_here}  yerdan {context.user_data['to_location']} "
        f"ga bergan buyurtmangiz qabul qiilindi."
        f" Masofa: {context.user_data['distance_km']} km. "
        f"Yo'l haqqi: {formatted_price} so'm. ",
        reply_markup= ReplyKeyboardMarkup(
        [
            [KeyboardButton("Buyurmani bekor qilish")]
        ],
        resize_keyboard=True,
    )
    )

    return CANCEL

def cancel(update, context):
    chat_id = update.effective_user.id
    text = update.message.text
    if text == "Buyurmani bekor qilish":
        order_id = context.user_data.get('order_id')
        db.delete_order(order_id)
        update.message.reply_text("Buyurtma bekor qilindi ❌")
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
