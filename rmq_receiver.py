import json
import asyncio
import aio_pika

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.payload import generate_payload, prepare_arg, prepare_attachment, prepare_file
from datetime import datetime

import config
from multiprocessing import Pool, Process

from loguru import logger


async def main(loop, bot_token, connection_string, rmq_channel, my_id):
    print(f"[{my_id}] Starting worker")
    connection = await aio_pika.connect_robust(
        connection_string, loop=loop
    )

    bot = Bot(token=bot_token)

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
                    now = datetime.now()
                    logger.debug(f"[{my_id}] - Worker received at {now} - {message.body}")

                    body = json.loads(message.body)
                    files = body.get('files')
                    if files:
                        files = {file["attach"]: types.InputFile(file["file_name"]) for file in files}
                    logger.debug(files)
                    await bot.request(body['method'],
                                        data = body.get('data'),
                                        files = files)
                    logger.debug(f"[{my_id}] - Worker sent at {datetime.now()} time spend {datetime.now() - now}")



def start_consumer(id):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, config.bot_token,
                                    config.rmq_connection_string,
                                    config.rmq_channel,
                                    id))
    loop.close()

if __name__ == "__main__":
    WORKER_NUMBER = 0
    workers = 5
    for i in range(0, workers, 1):
        WORKER_NUMBER += 1
        p = Process(target=start_consumer, args = (i,))
        p.start()
