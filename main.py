

import os
import json
import asyncio
import logging

from random import randint
from nats.aio.client import Client


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# App Settings
NATS_SERVERS = os.environ.get('NATS_SERVERS', 'nats://127.0.0.1:4222')


def get_webhooks(ids):
    webhook = 'https://hooks.slack.com/services/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'
    return [webhook for x in range(1, randint(1, 5))]

async def run(loop):
    client = Client()
    servers = NATS_SERVERS.split(',')

    await client.connect(io_loop=loop, servers=servers)
    logger.info('Connected to NATS server...')


    async def message_handler(msg):
        try:
            data = json.loads(msg.data.decode())
            webhooks = get_webhooks(data['ids'])

            logger.info('Got {} webhooks for killmail with ID {}.'.format(len(webhooks), data['zkb_data']['killID']))

            payload = {
                'webhooks': webhooks,
                'zkb_data': data['zkb_data'],
            }

            await client.publish('slack.format.webhook.zkillboard', str.encode(json.dumps(payload)))

        except Exception as e:
            logger.info('Got exception: {}'.format(e))

    await client.subscribe('zkillboard.processed.unique_ids', 'slack-zkb-lookup', message_handler)


if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(run(loop))
  loop.run_forever()








@app.route('/', methods=['POST'])
def message():
    message = request.json['message']

    data = json.loads(base64.b64decode(str(message['message']['data'])))

    PS_TOPIC.publish(json.dumps({
        'webhooks': ['https://hooks.slack.com/services/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'],
        'killmail': data['killmail'],
    }))
    
    return ('', 204)


@app.before_first_request
def setup_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
