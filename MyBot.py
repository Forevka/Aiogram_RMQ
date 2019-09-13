import json
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.bot import api
from aiogram.utils.payload import generate_payload, prepare_arg, prepare_attachment, prepare_file

import aio_pika
import config
from loguru import logger

def create_bot(rmq_channel, connection_string, **kwargs):
    bot = MyBot(rmq_channel, connection_string, **kwargs)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.connect(loop))
    return bot

def convert_to_dict(key, obj):
    #  Populate the dictionary with object meta data
    obj_dict = {
        "attach": key,
        "file_name": obj.file.name
    }

    return obj_dict

class MyBot(Bot):
    def __init__(self, rmq_channel, connection_string, **kwargs):
        self.token = kwargs['token']
        self.connection_string = connection_string
        self.connection = None
        self.rmq_channel = None
        self.rmq_channel_name = rmq_channel

        self.important_methods = ['getMe', 'getUpdates', 'getWebhookInfo']

        super().__init__(**kwargs)
        logger.debug('Initialized bot for ', self.token)

    async def connect(self, loop):
        self.connection = await aio_pika.connect_robust(self.connection_string,
                                                    loop=loop)
        self.rmq_channel = await self.connection.channel()

    async def request(self, method, data = None, files = None, **kwargs):
        logger.debug(method)
        if method in self.important_methods:
            return await api.make_request(self.session, self.token, method, data, files,
                                    proxy=self.proxy, proxy_auth=self.proxy_auth, timeout=self.timeout, **kwargs)
        else:
            if files:
                print(files)
                files = [convert_to_dict(key, item) for key, item in files.items()]
            body = {
              'method': method,
              'data': data,
              'files': files
            }
            logger.debug(body)
            await self.rmq_channel.default_exchange.publish(
                    aio_pika.Message(
                        body = json.dumps(body).encode('utf-8')
                    ),
                    routing_key=self.rmq_channel_name
                )
            if method == "sendMediaGroup":
                return [{"ok":True,"result":{}}]
            return {"ok":True,"result":{"url":"https://forevka.serveo.net:443/webhookbot_1","has_custom_certificate": False,"pending_update_count":0,"last_error_date":1565774252,"last_error_message":"Wrong response from the webhook: 502 Bad Gateway","max_connections":40}}
