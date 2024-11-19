#!/usr/bin/env python
import pika
import re
#from router_control import set_tunnel, set_accesslist, set_accesslist_tunnel
#from router_control import del_tunnel, del_accesslist, del_accesslist_tunnel
#from router_control import list_router, list_tunnel, list_accesslist, list_accesstunnel, list_tunnelaccess
import router_control_telnet
import router_control_ssh
from topology import set_router_params, del_router
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_router_queue, control_protocol

# RabbitMQ setup
if not config_rabbitmq(['ROUTER']):
    print("Error in config file.")
    exit()

print("RabbitMQ Server: " + rabbitmq_host())

PROTOCOL = control_protocol()
if PROTOCOL == None or PROTOCOL == "telnet":
    control = router_control_telnet.router_control_telnet()
if PROTOCOL == "ssh":
    control = router_control_ssh.router_control_ssh()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host()),
)
channel = connection.channel()

channel.queue_declare(queue=rabbitmq_router_queue(), durable=False)
print(" [*] Waiting for messages on " + rabbitmq_router_queue() + ". To exit press CTRL+C")

def send_return(queue_name, body):
    channel.basic_publish(exchange="", routing_key=queue_name, properties=pika.BasicProperties(expiration='10000',), body=body)

def callback(ch, method, properties, body):
    # print(f" [x] Received {body.decode()}")
    #try:
    if True:
        params = body.decode().split(';')
        if len(params) > 0:
            command = params[0]
            # print(f" [x] Receive Command: {command}")
            if command == 'list':
                if len(params) > 2:
                    listcmd = params[1]
                    client_queue = params[2]
                    channel.queue_declare(queue=client_queue, durable=False)
                    # print(f" [x] list;{listcmd} to {client_queue}")
                    if listcmd == 'router':
                        # list;router;<queue>
                        control.list_router(send_return, client_queue)
                    if listcmd == 'tunnel':
                        # list;tunnel;<queue>;<router.id>
                        if len(params) > 3:
                            router_id = params[3]
                            control.list_tunnel(send_return, client_queue, router_id)
                    if listcmd == 'accesslist':
                        # list;accesslist;<queue>;<router.id>
                        if len(params) > 3:
                            router_id = params[3]
                            control.list_accesslist(send_return, client_queue, router_id)
                    if listcmd == 'accesstunnel':
                        # list;accesstunnel;<queue>;<router.id>;<accesslist_id>
                        if len(params) > 4:
                            router_id = params[3]
                            accesslist_id = params[4]
                            control.list_accesstunnel(send_return, client_queue, router_id, accesslist_id)
                    if listcmd == 'tunnelaccess':
                        # list;tunnelaccess;<queue>;<tunnel.id>
                        if len(params) > 4:
                            router_id = params[3]
                            tunnel_id = params[4]
                            control.list_tunnelaccess(send_return, client_queue, router_id, tunnel_id)
                    # print(f" [x] Sent")
            if command == 'set':
                setcmd = params[1]
                router_id = params[2]
                if setcmd == 'router':
                    # set;router;<id>;<address>;<port>
                    if len(params) > 4:
                        address = params[3]
                        port = params[4]
                        user = ''
                        password = ''
                        if len(params) > 6:
                            user = params[5]
                            password = params[6]
                        set_router_params(router_id, address, port, user, password)
                        # print(f" [x] SET Router {router_id} => {address}:{port}:{user}:###########")
                if setcmd == 'tunnel':
                    # set;tunnel;<router.id>;<id>;<address>;<mask>;<path>[;<description>]
                    if len(params) > 6:
                        tunnel_id = params[3]
                        address= params[4]
                        mask = params[5]
                        path = params[6]
                        description = tunnel_id
                        if len(params) > 7:
                            description = params[7]
                        control.set_tunnel(router_id, tunnel_id, address, mask, path, description)
                        # print(f" [x] SET Tunnel {tunnel_id} = {address}/{mask} ( {path} ) \"{description}\"")
                if setcmd == 'accesslist':
                    # set;accesslist;<router.id>;<id>;<protocol>;<address_in>;<mask_in>;<address_out>;<mask_out>;<tos>
                    if len(params) > 9:
                        accesslist_id = params[3]
                        protocol = params[4]
                        address_in = params[5]
                        mask_in = params[6]
                        address_out = params[7]
                        mask_out = params[8]
                        tos = params[9]
                        control.set_accesslist(router_id, accesslist_id, protocol, address_in, mask_in, address_out, mask_out, tos)
                        # print(f" [x] SET Access List {accesslist_id} Protocol: {protocol} In: {address_in}/{mask_in} Out: {address_out}/{mask_out} ToS: {tos}")
                if setcmd == 'accesstunnel':
                    # set;accesstunnel;<router.id>;<accesslist.id>;<tunnel.id>
                    if len(params) > 4:
                        accesslist_id = params[3]
                        tunnel_id = params[4]
                        control.set_accesslist_tunnel(router_id, accesslist_id, tunnel_id)
                        # print(f" [x] SET Access Tunnel {accesslist_id} => {tunnel_id}")
            if command == 'del':
                if len(params) > 2:
                    delcmd = params[1]
                    router_id = params[2]
                    if delcmd == 'router':
                        # del;router;<router.id>
                        del_router(router_id)
                        # print(f" [x] DEL Router {router_id}")
                    if delcmd == 'tunnel':
                        # del;tunnel;<router.id>;<tunnel.id>
                        if len(params) > 3:
                            tunnel_id = params[3]
                            control.del_tunnel(router_id, tunnel_id)
                            # print(f" [x] DEL Tunnel {tunnel_name}")
                    if delcmd == 'accesslist':
                        # del;accesslist;<router.id>;<accesslist.id>
                        if len(params) > 3:
                            accesslist_id = params[3]
                            control.del_accesslist(router_id, accesslist_id)
                            # print(f" [x] DEL Access List {accesslist_id}")
                    if delcmd == 'accesstunnel':
                        # del;accesstunnel;<router.id>;<accesslist.id>
                        if len(params) > 3:
                            accesslist_id = params[3]
                            control.del_accesslist_tunnel(router_id, accesslist_id)
                            # print(f" [x] Unassign Access Tunnel {accesslist_id} to Tunnel")
    #except:
    #    print(" [x] Error")
    # print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)

queue_name=rabbitmq_router_queue()
channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_message_callback=callback, queue=queue_name)

channel.start_consuming()

