import json
import asyncio
import aio_pika

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.payload import generate_payload, prepare_arg, prepare_attachment, prepare_file

from MyBot import BotWorker
import config

async def main(loop, bot_token, connection_string, rmq_channel):
    connection = await aio_pika.connect_robust(
        connection_string, loop=loop
    )

    bot = BotWorker(token=bot_token)

    async with connection:
        # Creating channel
        channel = await connection.channel()

        # Declaring queue
        queue = await channel.declare_queue(
            rmq_channel, auto_delete=False
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print(" [x] Received %r" % message.body)

                    await bot.send_custom_request(message.body)

if __name__ == "__main__":
    print(' [*] Waiting for messages. To exit press CTRL+C')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, config.bot_token,
                                    config.rmq_connection_string,
                                    config.rmq_channel))
    loop.close()
