import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

from MyBot import create_bot
import config

vote_cb = CallbackData('vote', 'action')  # vote:<action>
likes = {}  # user_id: amount_of_likes

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher

bot = create_bot(config.rmq_channel, config.rmq_connection_string, token=config.bot_token)
dp = Dispatcher(bot)

def get_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('👍', callback_data=vote_cb.new(action='up')),
        types.InlineKeyboardButton('👎', callback_data=vote_cb.new(action='down')),
    )


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    amount_of_likes = likes.get(message.from_user.id, 0)  # get value if key exists else set to 0
    await message.reply(f'Vote! You have {amount_of_likes} votes now.', reply_markup=get_keyboard())


@dp.callback_query_handler(vote_cb.filter(action=['up', 'down']))
async def callback_vote_action(query: types.CallbackQuery, callback_data: dict):
    logging.info('Got this callback data: %r', callback_data)  # callback_data contains all info from callback data
    await query.answer()  # don't forget to answer callback query as soon as possible
    callback_data_action = callback_data['action']
    likes_count = likes.get(query.from_user.id, 0)

    if callback_data_action == 'up':
        likes_count += 1
    else:
        likes_count -= 1

    likes[query.from_user.id] = likes_count  # update amount of likes in storage

    await bot.edit_message_text(
        f'You voted {callback_data_action}! Now you have {likes_count} vote[s].',
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard(),
    )

@dp.message_handler(commands='kb')
async def start_cmd_handler(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=3)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    btns_text = ('Yes!', 'No!')
    keyboard_markup.row(*(types.KeyboardButton(text) for text in btns_text))
    # adds buttons as a new row to the existing keyboard
    # the behaviour doesn't depend on row_width attribute

    more_btns_text = (
        "I don't know",
        "Who am i?",
        "Where am i?",
        "Who is there?",
    )
    keyboard_markup.add(*(types.KeyboardButton(text) for text in more_btns_text))
    # adds buttons. New rows are formed according to row_width parameter

    await message.reply("Hi!\nDo you like aiogram?", reply_markup=keyboard_markup)

@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)

    await message.reply(message.text, reply=False)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
