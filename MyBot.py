import json
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.bot import api
from aiogram.utils.payload import generate_payload, prepare_arg, prepare_attachment, prepare_file

import aio_pika
import config

def create_bot(rmq_channel, connection_string, **kwargs):
    bot = MyBot(rmq_channel, connection_string, **kwargs)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.connect(loop))
    return bot

class MyBot(Bot):
    def __init__(self, rmq_channel, connection_string, **kwargs):
        self.token = kwargs['token']
        self.connection_string = connection_string
        self.connection = None
        self.rmq_channel = None
        self.rmq_channel_name = rmq_channel

        self.important_methods = ['getMe', 'getUpdates', 'getWebhookInfo']
        print('Initialized bot for ', self.token)

        super().__init__(**kwargs)

    async def connect(self, loop):
        self.connection = await aio_pika.connect_robust(self.connection_string,
                                                    loop=loop)
        self.rmq_channel = await self.connection.channel()

    async def request(self, method, data = None, files = None, **kwargs):
        print(method)
        if method in self.important_methods:
            return await api.make_request(self.session, self.token, method, data, files,
                                    proxy=self.proxy, proxy_auth=self.proxy_auth, timeout=self.timeout, **kwargs)
        else:
            await self.rmq_channel.default_exchange.publish(
                    aio_pika.Message(
                        body = json.dumps({
                          'method': method,
                          'data': data,
                          'files': files
                        }).encode('utf-8')
                    ),
                    routing_key=self.rmq_channel_name
                )
            return {"ok":True,"result":{"url":"https://forevka.serveo.net:443/webhookbot_1","has_custom_certificate": False,"pending_update_count":0,"last_error_date":1565774252,"last_error_message":"Wrong response from the webhook: 502 Bad Gateway","max_connections":40}}

class BotWorker(Bot):
    def __init__(self, **kwargs):
        self.token = kwargs['token']
        print(self.token)
        super().__init__(**kwargs)

    async def send_custom_request(self, body, **kwargs):
        body = json.loads(body)
        return await api.make_request(self.session, self.token, body['method'],
                                body.get('data'), body.get('files'),
                                proxy=self.proxy, proxy_auth=self.proxy_auth, timeout=self.timeout, **kwargs)
