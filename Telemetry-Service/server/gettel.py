#!/usr/bin/env python
import sys
from datetime import datetime
import pika
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_telemetry_queue, rabbitmq_client_queue
import os

SIZE_CACHE = 1000

if not config_rabbitmq(['TELEMETRY']):
    print("Error in config file.")
    exit()

print("RabbitMQ Server: " + rabbitmq_host())

CLIENT_QUEUE = rabbitmq_client_queue()
TELEMETRY_QUEUE = rabbitmq_telemetry_queue()

body = f"telemetry;get;{CLIENT_QUEUE};latency;*;-2m;*;1"

connection_cli = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host()),
)
channel_cli = connection_cli.channel()
channel_cli.queue_declare(queue=TELEMETRY_QUEUE, durable=False)
channel_cli.basic_publish(exchange="", routing_key=TELEMETRY_QUEUE, properties=pika.BasicProperties(expiration='10000',), body=body)



