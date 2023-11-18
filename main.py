# Description: Main file for bot logic and handlers (client side)
import asyncio
import logging

import tmdbsimple as tmdb
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
import telebot


import api
import config

tmdb.API_KEY = api.TMDB_API_KEY
bot = Bot(config.BOT_TOKEN)
dp = Dispatcher(bot=bot)
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'
bot2 = telebot.TeleBot(config.BOT_TOKEN)


# ========================================= Client side ========================================= #
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    bot_info = await bot.get_me()
    await message.answer(
        f"<b>Welcome to {bot_info.first_name}.</b>\n 🇬🇧 Please select language \n 🇺🇦 Будь ласка, виберіть мову \n "
        f"🇷🇺 Пожалуйста, выберите язык", reply_markup=language_keyboard(), parse_mode=ParseMode.HTML)


# ========================================= Language =========================================  #
user_languages = {}


@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    await message.answer("Please select language:", reply_markup=language_keyboard())


@dp.callback_query(lambda query: query.data.startswith('set_language'))
async def set_language_callback(query: types.CallbackQuery):
    language_code = query.data.split('_')[2]
    set_user_language(query.from_user.id, language_code)
    next_action_message = get_next_action_message(language_code)
    await bot.send_message(query.from_user.id, next_action_message, reply_markup=menu_keyboard(language_code),
                           parse_mode=ParseMode.HTML)
    await bot.answer_callback_query(query.id, f"Language set to {language_code}")

    # Remove the menu buttons
    await bot.edit_message_reply_markup(query.from_user.id, query.message.message_id)


dp.callback_query(lambda query: query.data.startswith('menu_option'))


@dp.callback_query(lambda query: query.data.startswith('menu_option'))
async def set_menu_callback(query: types.CallbackQuery):
    menu_code = query.data.split('_')[2]
    language_code = query.data.split('_')[3]

    if menu_code == '1' or menu_code == '2':
        keyboard_markup = submenu_keyboard(language_code)
        await bot.edit_message_text("Please select an option:",
                                    chat_id=query.from_user.id,
                                    message_id=query.message.message_id,
                                    reply_markup=keyboard_markup)
    elif menu_code == '3':
        await bot.send_message(query.from_user.id, "You selected the third menu option.")
    elif menu_code == '4':
        await bot.send_message(query.from_user.id, "You selected the fourth menu option.")


@bot2.callback_query_handler(func=lambda call: call.data.startswith('submenu_option'))
def set_submenu_callback(call):
    submenu_code = call.data.split('_')[2]
    language_code = call.data.split('_')[3]

    if submenu_code == '1':
        # Fetch popular movies
        movies = tmdb.Movies()
        popular_movies = movies.popular(language=language_code)

        # Send a message with the title and poster of each movie
        for movie in popular_movies['results']:
            title = movie['title']
            poster_url = 'https://image.tmdb.org/t/p/w500' + movie['poster_path']
            bot.send_photo(call.message.chat.id, photo=poster_url, caption=title)


def get_next_action_message(language_code):
    messages = {
        'en': '<b>Menu\n</b>Please select the next action:',
        'ua': '<b>Меню\n</b>Будь ласка, виберіть наступну дію:',
        'ru': '<b>Меню\n</b>Пожалуйста, выберите следующее действие:',
    }
    return messages.get(language_code, 'Please select the next action')


def language_keyboard():
    keyboard = [[types.InlineKeyboardButton(text='🇬🇧 English', callback_data='set_language_en')],
                [types.InlineKeyboardButton(text='🇺🇦 Українська', callback_data='set_language_ua')],
                [types.InlineKeyboardButton(text='🇷🇺 Русский', callback_data='set_language_ru')], ]

    keyboard_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    return keyboard_markup


def menu_keyboard(language_code):
    options = {
        'en': ['Movies', 'Series', 'Randomizer', 'Saved'],
        'ua': ['Фільми', 'Серіали', 'Рандомайзер', 'Збережене'],
        'ru': ['Фильмы', 'Сериалы', 'Рандомайзер', 'Сохранённое'],
    }

    option_texts = options.get(language_code, options[language_code])

    keyboard = [
        [
            types.InlineKeyboardButton(text=option_texts[0], callback_data=f'menu_option_1_{language_code}'),
            types.InlineKeyboardButton(text=option_texts[1], callback_data=f'menu_option_2_{language_code}'),
        ],
        [
            types.InlineKeyboardButton(text=option_texts[2], callback_data=f'menu_option_3_{language_code}'),
            types.InlineKeyboardButton(text=option_texts[3], callback_data=f'menu_option_4_{language_code}'),
        ]
    ]
    keyboard_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    return keyboard_markup


def submenu_keyboard(language_code):
    options = {
        'en': ['Popular Now', 'By TMDB Rating', 'By Genre'],
        'ua': ['Популярне зараз', 'За рейтингом TMDB', 'За жанром'],
        'ru': ['Популярно сейчас', 'По рейтингу TMDB', 'По жанру'],
    }

    option_texts = options.get(language_code, options['en'])

    keyboard = [
        [types.InlineKeyboardButton(text=option_texts[0], callback_data=f'submenu_option_1_{language_code}')],
        [types.InlineKeyboardButton(text=option_texts[1], callback_data=f'submenu_option_2_{language_code}')],
        [types.InlineKeyboardButton(text=option_texts[2], callback_data=f'submenu_option_3_{language_code}')]

    ]
    keyboard_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    return keyboard_markup


def set_user_language(user_id, language_code):
    user_languages[user_id] = language_code


# =========================================  Help =========================================  #
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Welcome, please choose your language:")


# ========================================= Testing and Exception Handling =========================================
async def testing():
    global bot
    try:
        logging.basicConfig(level=logging.INFO)

        bot = Bot(token=config.BOT_TOKEN)
        polling_task = asyncio.create_task(dp.start_polling(bot))
        await polling_task
    except Exception as e:
        logging.exception("An error occurred:")
    finally:
        logging.info("Bot stopped.")


async def main():
    await testing()


if __name__ == '__main__':
    asyncio.run(main())
