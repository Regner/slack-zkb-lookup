

import os
import json
import pika
import random
import logging
import requests


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# App Settings
RABBITMQ_SERVER = os.environ.get('RABBITMQ_SERVER', 'rabbitmq')
SLACK_LOOKUP = os.environ.get('SLACK_WEBHOOKS_LOOKUP', 'http://settings-slack-webhooks/api/settings/slack/webhooks/lookup/')

# RabbitMQ Setup
connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_SERVER))
channel = connection.channel()

channel.exchange_declare(exchange='regner', type='topic')
channel.queue_declare(queue='slack-zkb-lookup', durable=True)
channel.queue_bind(exchange='regner', queue='slack-zkb-lookup', routing_key='zkillboard.raw')
logger.info('Connected to RabbitMQ server...')


def find_entity_ids(entity):
    ids = set()

    if 'character' in entity:
        ids.add(entity['character']['id'])

    if 'corporation' in entity:
        ids.add(entity['corporation']['id'])

    if 'alliance' in entity:
        ids.add(entity['alliance']['id'])

    if 'faction' in entity:
        ids.add(entity['faction']['id'])

    if 'shipType' in entity:
        ids.add(entity['shipType']['id'])

    if 'weaponType' in entity:
        ids.add(entity['weaponType']['id'])

    return ids


def find_unique_ids(killmail):
    ids = set()

    ids = ids.union(find_entity_ids(killmail['victim']))

    for attacker in killmail['attackers']:
        ids = ids.union(find_entity_ids(attacker))

    return ids


def callback(ch, method, properties, body):
    data = json.loads(body.decode())

    ids = find_unique_ids(data['killmail'])
    params = {
        'ids': ids,
        'value': data['zkb']['totalValue'],
    }

    response = requests.get(SLACK_LOOKUP, params=params)
    if response.status_code != requests.codes.ok:
        print(response.text)
        return

    webhooks = response.json()

    for webhook in webhooks:
        payload = {
            'webhook': webhook,
            'zkb_data': data,
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
    logging.info('Processed killmail with ID {}.'.format(data['killmail']['killID']))


channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='slack-zkb-lookup')
channel.start_consuming()
