import logging
from textwrap import dedent
import time

import redis
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from environs import Env
from email_validator import validate_email, EmailNotValidError

from shop_access import get_bearer_access_token
from shop_access import get_products_list, get_product_by_id
from shop_access import add_product_to_cart, get_cart_items, remove_cart_items
from shop_access import create_customer

env = Env()
env.read_env()

_database = None
bearer_token_time = 0
bearer_token = None
client_id = env('CLIENT_ID')
client_secret = env('CLIENT_SECRET_TOKEN')


def start(bot, update):
    query = update.callback_query

    if query:
        chat_id = query.message.chat_id
    else:
        chat_id = update.message.chat_id

    check_bearer_token()
    products = get_products_list(bearer_token=bearer_token)
    reply_markup = get_menu_keyboard(products)
    bot.send_message(chat_id=chat_id, text='Please choose:',
                     reply_markup=reply_markup)
    if query:
        bot.delete_message(chat_id=chat_id, 
                           message_id=query.message.message_id)

    return 'HANDLE_MENU'


def handle_menu(bot, update):
    check_bearer_token()

    query = update.callback_query
    chat_id = query.message.chat_id

    product_id = query.data
    product = get_product_by_id(bearer_token=bearer_token,
                                product_id=product_id)

    measures = ['1', '2', '5']
    product_keyboard = [
        [InlineKeyboardButton(f'{weight} kg', callback_data=f'{weight},{product_id}') for weight in measures],
        [InlineKeyboardButton('Cart', callback_data='cart')],
        [InlineKeyboardButton('Menu', callback_data='menu')],
        [InlineKeyboardButton('Payment', callback_data='payment')]
        ]
    reply_markup = InlineKeyboardMarkup(product_keyboard)

    message = dedent(f'''
    {product['name']}

    {product['price']} per kg
    {product['stock']} on stock

    {product['description']}
    ''')

    bot.send_photo(chat_id=chat_id, photo=product['image_url'],
                   caption=message, reply_markup=reply_markup)
    bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)

    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update):
    check_bearer_token()

    query = update.callback_query
    chat_id = query.message.chat_id

    quantity, product_id = query.data.split(',')

    add_product_to_cart(bearer_token=bearer_token,
                        product_id=product_id,
                        quantity=quantity,
                        chat_id=chat_id)
    message = f'Add {quantity} kg'
    bot.answer_callback_query(callback_query_id=query.id, text=message)

    return 'HANDLE_DESCRIPTION'


def handle_cart(bot, update):
    check_bearer_token()
    query = update.callback_query
    chat_id = query.message.chat_id

    if 'remove' in query.data:
        product_id = query.data.split(',')[1]
        remove_cart_items(bearer_token=bearer_token, 
                          product_id=product_id, 
                          chat_id=chat_id)

    message = ''
    cart_keyboard = []
    cart, total_amount = get_cart_items(bearer_token=bearer_token, 
                                        chat_id=chat_id)

    for product in cart:
        cart_keyboard.append([InlineKeyboardButton(
            f"Remove from cart {product['name']}", 
            callback_data=f"remove,{product['id']}")])

        product_output = dedent(f'''
            {product['name']}
            {product['description']}
            {product['price']} per kg
            {product['quantity']} kg in cart for {product['amount']}
            ''')
        message += product_output

    cart_keyboard.append([InlineKeyboardButton('Menu', callback_data='menu')])
    cart_keyboard.append([InlineKeyboardButton('Payment', callback_data='payment')])
    reply_markup = InlineKeyboardMarkup(cart_keyboard)
    message += f'\nTotal: {total_amount}'

    bot.send_message(chat_id=chat_id, 
                     text=message, 
                     reply_markup=reply_markup)
    bot.delete_message(chat_id=query.message.chat_id, 
                       message_id=query.message.message_id)

    return 'HANDLE_CART'


def waiting_email(bot, update):
    query = update.callback_query
    bot.send_message(chat_id=query.message.chat_id, 
                     text='Please send your email')

    return 'HANDLE_USER'


def handle_user(bot, update):
    check_bearer_token()
    user_name = f'{update.effective_user.first_name}_{update.effective_chat.id}'
    shop_password = f'{update.effective_chat.id}'

    try:
        valid = validate_email(update.message.text)
        email = valid.email
    except EmailNotValidError:
        update.message.reply_text('Sorry, but we cannot valid your email. Please try again')
        return 'HANDLE_USER'

    keyboard = [[InlineKeyboardButton('Continue shopping', callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    create_customer(bearer_token=bearer_token, 
                    username=user_name,
                    email=email,
                    password=shop_password)

    update.message.reply_text('Thank you for order. We will be contanting you soon',
                              reply_markup=reply_markup)

    return 'HANDLE_MENU'


def handle_users_reply(bot, update):
    query = update.callback_query
    db = get_database_connection()

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif query:
        user_reply = query.data
        chat_id = query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'cart':
        user_state = 'HANDLE_CART'
    elif user_reply == 'payment':
        user_state = 'WAITING_EMAIL'
    elif user_reply == 'menu':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': waiting_email,
        'HANDLE_USER': handle_user,
    }

    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.exception(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = env("DATABASE_PASSWORD")
        database_host = env("DATABASE_HOST")
        database_port = env("DATABASE_PORT")

        _database = redis.Redis(host=database_host,
                                port=database_port,
                                password=database_password)
    return _database


def check_bearer_token():
    global bearer_token_time
    global bearer_token

    curent_time = time.time()
    if curent_time >= bearer_token_time:
        bearer_token, bearer_token_time = get_bearer_access_token(client_id=client_id)


def get_menu_keyboard(products):
    products_keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products
        ]
    products_keyboard.append([InlineKeyboardButton('Cart', callback_data='cart')])
    return InlineKeyboardMarkup(products_keyboard)


if __name__ == '__main__':
    token = env("TELEGRAM_TOKEN")
    logging.basicConfig(format="%(process)d %(levelname)s %(message)s",
                        level=logging.WARNING)

    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()