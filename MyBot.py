from aiogram import Bot, Dispatcher, executor, types
from aiogram.bot import api
from aiogram.utils.payload import generate_payload, prepare_arg, prepare_attachment, prepare_file

import json

class MyBot(Bot):
    def __init__(self, rmq_channel, **kwargs):
        self.token = kwargs['token']
        self.rmq_channel = rmq_channel
        self.important_methods = ['getMe', 'getUpdates', 'getWebhookInfo']
        print(self.token)
        super().__init__(**kwargs)

    async def request(self, method, data = None, files = None, **kwargs):
        print(method)
        if method in self.important_methods:
            return await api.make_request(self.session, self.token, method, data, files,
                                    proxy=self.proxy, proxy_auth=self.proxy_auth, timeout=self.timeout, **kwargs)
        else:
            self.rmq_channel.basic_publish(exchange='',
                                      routing_key='hello',
                                      body = json.dumps({
                                        'method': method,
                                        'data': data,
                                        'files': files
                                      }))
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
