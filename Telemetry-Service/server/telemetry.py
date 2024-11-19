#!/usr/bin/env python
import sys
from datetime import datetime
import pika
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_telemetry_queue
import os

SIZE_CACHE = 1000

if not config_rabbitmq(['TELEMETRY']):
    print("Error in config file.")
    exit()

print("RabbitMQ Server: " + rabbitmq_host())

def send_mq_client(client_queue, body):
    connection_cli = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_host()),
    )
    channel_cli = connection_cli.channel()
    channel_cli.queue_declare(queue=client_queue, durable=False)
    channel_cli.basic_publish(exchange="", routing_key=client_queue, properties=pika.BasicProperties(expiration='10000',), body=body)

def set_data(datalake, timestamp, data_index, value):
    item = datalake.get(data_index, None)
    if item == None:
        item = {}
    keys = item.keys()
    if len(keys)>(SIZE_CACHE):
        item.pop(keys[0])
    try:
        ftimestamp = float(timestamp)
        fvalue = float(value)
    except:
        fvalue = 0.0
    item.update({ ftimestamp: fvalue })
    datalake.update( { data_index: item } )

def get_point(previous_value, next_value, previous_time, next_time, actual_time):
    delta_time = next_time - previous_time
    delta_value = next_value - previous_value
    delta_actual = actual_time - previous_time
    diff = delta_actual / delta_time * delta_value
    actual_value = previous_value + diff
    return actual_value

def get_data(datalake, index, start_time, end_time, interval):
    # index == '*' => all indexes
    result = {}
    if index == '*':
        index_array = datalake.keys()
    else:
        index_array = [ index ]
    for data_index in index_array:
        data_result = {}
        cache = datalake.get(data_index)
        if cache != None:
            cache_lst = [*cache.items()]
            count = 0
            while count<len(cache_lst) and start_time < cache_lst[count][0]:
                previous_time = cache_lst[count][0]
                previous_value = cache_lst[count][1]
                count = count + 1
            if count<len(cache_lst) and start_time >= cache_lst[count][0]:
                actual_time = start_time
                while count<len(cache_lst) and end_time > cache_lst[count][0]:
                    next_time = cache_lst[count][0]
                    next_value = cache_lst[count][1]
                    while actual_time < cache_lst[count][0]:
                        # value (interpolate)
                        #  <previous_time>.....<actual_time>.....<actual_time+n>.....<next_time>
                        actual_value = get_point(previous_value, next_value, previous_time, next_time, actual_time)
                        data_result.update({ actual_time: actual_value})
                        actual_time = actual_time + interval
                    previous_time = cache_lst[count][0]
                    previous_value = cache_lst[count][1]
                    count = count + 1
        result.update( { data_index: data_result } )
    return result

def stringtime(timestamp):
    # time values
    #    * = now
    #    -<val><time> = back in time, where val=number and time=h(hour),m(minute),s(second)
    #        ex: -3m  (now - 3 minutes)
    #            -40s (now - 40 seconds)
    if timestamp == '*':
        result = datetime.timestamp(datetime.now())
    else:
        if timestamp[0:1] == '-':
            val = timestamp[1:-1]
            uni = timestamp[-1:]
            factor = 0
            if uni == 's':
                factor = 1
            if uni == 'm':
                factor = 60
            if uni == 'h':
                factor = 3600
            try:
                value = float(val)
            except:
                value = 0
            result = datetime.timestamp(datetime.now()) - ( value * factor )
        else:
            try:
                result = float(timestamp)
            except:
                result = 0
    return result

def callback_telemetry(ch, method, properties, body):
    print(f" [#] Received {body.decode()}")
    params = body.decode().split(';')
    if len(params) > 0:
        command = params[0].strip()
        if command == 'telemetry':
            if params[1].strip() == 'set':
                if params[2].strip() == 'latency':
                    if len(params) >= 5:
                        #[0]telemetry;[1]set;[2]latency;[3]<tunnel-name>;[4]<latency>;[5]<timestamp>
                        tunn = params[3]
                        ltnc = params[4]
                        tims = params[5]
                        set_data(LATENCY_DATA, tims, tunn, ltnc)
                if params[2].strip() == 'bandwidth':
                    if len(params) >= 6:
                        #[0]telemetry;[1]set;[2]bandwidth;[3]<node>;[4]<ethernet>;[5]<bps>;[6]<timestamp>
                        node = params[3]
                        ethv = params[4]
                        btps = params[5]
                        tims = params[6]
                        set_data(BANDWIDTH_DATA, tims, node + ":" + ethv, btps)
                if params[2].strip() == 'flowrate':
                    if len(params) >= 5:
                        #[0]telemetry;[1]set;[2]flowrate;[3]<tunnel-name>;[4]<flow-rate>;[5]<timestamp>
                        tunn = params[3]
                        flow = params[4]
                        tims = params[5]
                        set_data(FLOWRATE_DATA, tims, tunn, flow)
            if params[1].strip() == 'get':
                if len(params) >= 7:
                    client_queue = params[2].strip()
                    telemetry_type = params[3].strip()
                    index_name = params[4].strip()
                    start_time = stringtime(params[5].strip())
                    end_time = stringtime(params[6].strip())
                    interval = stringtime(params[7].strip())
                    result = None
                    if telemetry_type == 'latency':
                        #[0]telemetry;[1]get;[2]<client-queue>;[3]latency;[4]<index-name>[5]<start-time>;[6]<end-time>;[7]<interval-in-seconds>
                        result = get_data(LATENCY_DATA, index_name, start_time, end_time, interval)
                    if telemetry_type == 'bandwidth':
                        #[0]telemetry;[1]get;[2]<client-queue>;[3]bandwidth;[4]<index-name>[5]<start-time>;[6]<end-time>;[7]<interval-in-seconds>
                        result = get_data(BANDWIDTH_DATA, index_name, start_time, end_time, interval)
                    if telemetry_type == 'flowrate':
                        #[0]telemetry;[1]get;[2]<client-queue>;[3]flowrate;[4]<index-name>[5]<start-time>;[6]<end-time>;[7]<interval-in-seconds>
                        result = get_data(FLOWRATE_DATA, index_name, start_time, end_time, interval)
                    if result != None:
                        for name, val_dict in result.items():
                            result_text_list = []
                            for f in val_dict.values():
                                result_text_list.append(str(f))
                            result_list = ",".join(result_text_list)
                            body = "telemetry;" + telemetry_type + ";" + name + ";" + str(start_time) + ";" + str(end_time) + ";" + str(interval) + ";" + result_list
                            send_mq_client(client_queue, body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

LATENCY_DATA = {}
BANDWIDTH_DATA = {}
FLOWRATE_DATA = {}

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host()),
)
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_telemetry_queue(), durable=False)
print(" [*] Waiting for messages on " + rabbitmq_telemetry_queue() + ". To exit press CTRL+C")

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_message_callback=callback_telemetry, queue=rabbitmq_telemetry_queue())
channel.start_consuming()

