#!/usr/bin/env python
import sys
from freertr_polka import freertr_polka

def print_help():
    print("Param error, use:")
    print("-l                                                    # list routers")
    print("-s <router.id> <address> <port> [ <user> <password> ] # set router params")
    print("-d <router.id>                                        # delete router")
    print("")
    print("ex:")
    print("-s MIA localhost 2306")
    print("-s AMS localhost 2307")
    print("-s CAL localhost 22 user password")
    exit()
options = '-l0-s3-s5-d1'

# at least one option
num_params = len(sys.argv)-2
if num_params < 0:
    print_help()

# sane parameters
param = f"{sys.argv[1]}{num_params}"
if options.find(param) < 0:
    print_help()

freertr = freertr_polka()
if freertr != None:
    if sys.argv[1] == '-l':
        freertr.router_list()
    if sys.argv[1] == '-s':
        router_id = sys.argv[2]
        address = sys.argv[3]
        port = sys.argv[4]
        user = None
        if num_params > 3:
            user = sys.argv[5]
            password = sys.argv[6]
        freertr.router_set(router_id,address,port,user,password)
        print(f" [x] SET Router {router_id} {address}:{port}")
    if sys.argv[1] == '-d':
        router_id = sys.argv[2]
        freertr.router_del(router_id)
    freertr.close()
