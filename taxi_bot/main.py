import os
from handlers.user import *
from handlers.driver import *
from keyboards import *
from utils import *
from handlers.admin import *


TOKEN='YOUR TOKEN'


def main():
    db.create_table()
    seed_tariffs()
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text, get_name)],
            PHONE: [MessageHandler(Filters.contact, get_phone)],
            LANGUAGE: [CallbackQueryHandler(get_language)],
            WHO: [MessageHandler(Filters.text, who)],
            MODEL: [MessageHandler(Filters.text, car_model)],
            NUMBER: [MessageHandler(Filters.text, car_number)],
            D_TARIFF: [CallbackQueryHandler(tariff_callback_d)],
            ASSIGN: [MessageHandler(Filters.text, assaign_drivers)],
            COMPLETED: [MessageHandler(Filters.text, completed)],
            CANCEL: [MessageHandler(Filters.text, cancel)],

            MAIN_MENU: [MessageHandler(Filters.text, main_menu_select)],
            SETTING: [ MessageHandler(Filters.text, setting_select)],

            FROM_LOCATION:[MessageHandler(Filters.location, get_from_location)],
            TO_LOCATION: [MessageHandler(Filters.text & ~Filters.command, get_to_location)],
            TARIFF: [CallbackQueryHandler(tariff_callback)],

    },
    fallbacks=[]
    )

    admin_conv = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_login)],
        states={
            ADMIN_PASSWORD_ST: [MessageHandler(Filters.text & ~Filters.command, check_admin_password)],
            ADMIN_MENU: [MessageHandler(Filters.text & ~Filters.command, admin_menu_select)],

        },
        fallbacks=[CommandHandler('cancel', admin_logout)]
    )

    dp.add_handler(conv)
    dp.add_handler(admin_conv)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

