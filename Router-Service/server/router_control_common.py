# Control strings used to manage the edge routers
from topology import get_router_list
VRF_NAME = "CORE"

def control_string(string_id, params):
    result = ""
    if string_id == 'SHOW_CONFIG':
        result = [ "show running-config" ]
    if string_id == 'SET_TUNNEL':
        result = [ "delete interface " + params.get('tunnel_id'),
                   "config",
                   "interface " + params.get('tunnel_id'),
                   " description " + params.get('description') + "\n"
                   " tunnel vrf " + VRF_NAME,
                   " tunnel source loopback0",
                   " tunnel destination " + params.get('ip_dest'),
                   " tunnel domain-name " + params.get('ip_list'),
                   " tunnel mode polka",
                   " vrf forwarding " + VRF_NAME,
                   " ipv4 address " + params.get('address') + " " + params.get('mask'),
                   " no shutdown",
                   " no log-link-change",
                   " exit",
                   "exit" ]
    if string_id == 'SET_ACCESSLIST':
        result = [ "delete access-list " + params.get('accesslist_id'),
                   "config",
                   "access-list " + params.get('accesslist_id'),
                   " sequence 10 permit " + params.get('protocol_num') + " " + params.get('address_in') + " " + params.get('mask_in') + " "
                   "all " + params.get('address_out') + " " + params.get('mask_out') + " all" + params.get('cfg_tos'),
                   "exit",
                   "exit" ]
    if string_id == 'SET_ACCESSLIST_TUNNEL':
        result = [ "config",
                   "ipv4 pbr " + VRF_NAME +" sequence " + params.get('seq') + " " + params.get('accesslist_id') + " " + VRF_NAME + " nexthop " + params.get('ip_destiny'),
                   "exit",
                   "exit" ]
    if string_id == 'DEL_TUNNEL':
        result = [ "delete interface " + params.get('tunnel_id') ]
    if string_id == 'DEL_SEQUENCE':
        result = [ "config",
                   "no ipv4 pbr "  + VRF_NAME + " sequence " + str(params.get('seq')) + " " + str(params.get('accesslist_id')) + " "  + VRF_NAME,
                   "exit" ]
    if string_id == 'DEL_ACCESSLIST':
        result = [ "delete access-list " + str(params.get('accesslist_id')),
                   "exit" ]
    if string_id == 'DEL_ACCESSLIST_TUNNEL':
        result = [ "config",
                   "no ipv4 pbr "  + VRF_NAME + " sequence " + str(params.get('seq')) + " " + str(params.get('accesslist_id')) + " " +  + VRF_NAME,
                   "exit",
                   "exit" ]
    result = [ "terminal length 100000" ] + result
    return result

def list_router():
    list_txt = []
    router_list = get_router_list()
    if len(router_list) > 0:
        for key, value in router_list.items():
            router_txt = key + ',' + value['address'] + ':' + value['port']
            if value['user'] != None:
                router_txt = router_txt + ',' + value['user']
            list_txt.append(router_txt)
    return ';'.join(list_txt)

# parse and return structured data from freertr running config strings
def get_accesslist_tunnels(config):
    accesslist_dict = {}
    tunnel_dict = {}
    tunnel_id = ''
    for line in config:
        rs = line.split()
        if len(rs) > 0:
            if rs[0] == 'access-list':
                if len(rs) > 1:
                    accesslist_dict.update( { rs[1]: { 'seq': 0, 'ip': '' } } )
            if rs[0] == 'ipv4':
                if len(rs) > 1:
                    if rs[1] == 'pbr':
                        pbr = line.split(' ')
                        try:
                            seq = int(pbr[4])
                        except:
                            seq = 0
                        if seq > 0:
                            accesslist_dict.update( { pbr[5]: { 'seq': seq, 'ip': pbr[8] } } )
            if rs[0] == 'interface':
               if len(rs) > 1:
                   tunnel_id = rs[1]
                   route_list = []
                   dest_ip = ''
            if rs[0] == 'tunnel':
                if len(rs) >= 3:
                    if rs[1] == 'mode' and rs[2] == 'polka':
                        cfg_tunnel = True
                    if rs[1] == 'destination':
                        dest_ip = rs[2]
                    if rs[1] == 'domain-name':
                        cont_ip = 2
                        while cont_ip < len(rs):
                            route_list.append(rs[cont_ip])
                            cont_ip+=1
            if rs[0] == 'exit':
                cfg_tunnel = False
                tunnel_id = ''
            if rs[0] == 'ipv4':
                if len(rs) >= 3 and cfg_tunnel:
                    if rs[1] == 'address':
                        ip = rs[2]
                        mask = rs[3]
                        tunnel_dict.update( { tunnel_id: { 'ip': ip, 'mask': mask, 'route': '-'.join(route_list) + '-' + dest_ip } } )
    return(accesslist_dict, tunnel_dict)

