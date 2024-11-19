#!/usr/bin/env python
import sys
from freertr_polka import freertr_polka

def print_help():
    print("Param error, use:")
    print("-l <router_id>                                            # list tunnels")
    print("-s <router_id> <tunnel_id> <addr> <mask> <path> [<descr>] # set tunnel parameters")
    print("-d <router_id> <tunnel_id>                                # delete tunnel")
    print("-a <router_id> <tunnel_id>                                # list access lists assign to tunnel")
    print("")
    print("path = nodelist <node>[,<node>]...")
    exit()
options = '-l1-s5-s6-d2-a2'

# at least one option
num_params = len(sys.argv)-2
if num_params < 0:
    print_help()

# sane parameters
param = f"{sys.argv[1]}{num_params}"
if options.find(param) < 0:
    print_help()

# get router.id and set client channel
router_id = sys.argv[2]

freertr = freertr_polka()
if freertr != None:
    if sys.argv[1] == '-l':
        freertr.tunnel_list(router_id)
    if sys.argv[1] == '-a':
        tunnel_id = sys.argv[3]
        freertr.tunnel_accesslist(router_id, tunnel_id)
    if sys.argv[1] == '-s':
        tunnel_id = sys.argv[3]
        address = sys.argv[4]
        mask = sys.argv[5]
        path = sys.argv[6]
        description = tunnel_id
        if num_params == 6:
            description = sys.argv[7]
        freertr.tunnel_set(router_id, tunnel_id, address, mask, path, description)
        print(f" [x] Router [{router_id}] SET Tunnel {tunnel_id} {address}/{mask} = {path} \"{description}\"")
    if sys.argv[1] == '-d':
        tunnel_id = sys.argv[3]
        print(f" [x] Router [{router_od}] DEL Tunnel {tunnel_id}")
    freertr.close()