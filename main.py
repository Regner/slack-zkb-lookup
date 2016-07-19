

import os
import json
import pika
import random
import logging


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# App Settings
RABBITMQ_SERVER = os.environ.get('RABBITMQ_SERVER', 'rabbitmq-alpha')

# RabbitMQ Setup
connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_SERVER))
channel = connection.channel()

channel.exchange_declare(exchange='regner', type='topic')
channel.queue_declare(queue='slack-zkb-lookup', durable=True)
channel.queue_bind(exchange='regner', queue='slack-zkb-lookup', routing_key='zkillboard.processed.unique_ids')
logger.info('Connected to RabbitMQ server...')


def callback(ch, method, properties, body):
    data = json.loads(body.decode())

    webhooks = ['https://hooks.slack.com/services/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']

    for webhook in webhooks:
        payload = {
            'webhook': webhook,
            'kill': random.choice([True, False]),
            'zkb_data': data['zkb_data'],
        }

        channel.basic_publish(
            exchange='regner',
            routing_key='slack.format.webhook.zkillboard',
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode = 2,
            ),
        )

    ch.basic_ack(delivery_tag = method.delivery_tag)
    logging.info('Processed killmail with ID {}.'.format(data['zkb_data']['killID']))


channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='slack-zkb-lookup')
channel.start_consuming()
