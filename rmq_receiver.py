#!/usr/bin/env python
import pika
import json
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.payload import generate_payload, prepare_arg, prepare_attachment, prepare_file

from MyBot import BotWorker

API_TOKEN = '631844699:AAEVFt1lUrpQGaDiDZ7NpbunNRWezY8nXn0'

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

# Initialize bot
bot = BotWorker(token=API_TOKEN)

def callback(ch, method, properties, body):
    print(bot)
    print(" [x] Received %r" % body)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.send_custom_request(body))


channel.basic_consume(
    queue='hello', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')

channel.start_consuming()
