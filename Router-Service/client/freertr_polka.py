#!/usr/bin/env python
import pika
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_router_queue, rabbitmq_client_queue

class freertr_polka():
    def __init__(self, queueName = None):
        # RabbitMQ setup
        if not config_rabbitmq(['ROUTER','CLIENT']):
            print("Error in config file.")
            exit()

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host()),
        )

        # set channel
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=rabbitmq_router_queue(), durable=False)
        if queueName == None:
            self.CLIENT_QUEUE=rabbitmq_client_queue()
        else:
            self.CLIENT_QUEUE = queueName

    def close(self):
        self.connection.close()

#### ROUTER

    def router_list(self):
        command = f"list;router;{self.CLIENT_QUEUE}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def router_set(self, router_id, address, port, user = None, password = None):
        userpass = ''
        if user != None:
            userpass = ';' + user + ';' + password
        command = f"set;router;{router_id};{address};{port}{userpass}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def router_del(self, router_id):
        command = f"del;router;{router_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

#### TUNNEL

    def tunnel_list(self, router_id):
        command = f"list;tunnel;{self.CLIENT_QUEUE};{router_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def tunnel_accesslist(self, router_id, tunnel_id):
        command = f"list;tunnelaccess;{self.CLIENT_QUEUE};{router_id};{tunnel_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def tunnel_set(self, router_id, tunnel_id, address, mask, path, description = None):
        if description == None:
            description = ''
        command = f"set;tunnel;{router_id};{tunnel_id};{address};{mask};{path};{description}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def tunnel_del(self, router_id, tunnel_id):
        command = f"del;tunnel;{router_id};{tunnel_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

#### ACCESS LIST

    def accesslist_list(self, router_id):
        command = f"list;accesslist;{self.CLIENT_QUEUE};{router_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def accesslist_set(self, router_id, accesslist_id, protocol, address_in, mask_in, address_out, mask_out, tos):
        command = f"set;accesslist;{router_id};{accesslist_id};{protocol};{address_in};{mask_in};{address_out};{mask_out};{tos}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def accesslist_del(self, router_id, accesslist_id):
        command = f"del;accesslist;{router_id};{accesslist_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def accesslist_tunnel_assigned(self, router_id, accesslist_id):
        command = f"list;accesstunnel;{self.CLIENT_QUEUE};{router_id};{accesslist_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def accesslist_assign(self, router_id, accesslist_id, ip_destiny):
        command = f"set;accesstunnel;{router_id};{accesslist_id};{ip_destiny}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

    def accesslist_unassign(self, router_id, accesslist_id):
        command = f"del;accesstunnel;{router_id};{accesslist_id}"
        self.channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
