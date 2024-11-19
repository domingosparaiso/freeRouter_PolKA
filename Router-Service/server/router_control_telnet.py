#!/usr/bin/env python
import asyncio
import telnetlib3
from topology import get_router_list, get_router_host, get_router_port, get_router_user, get_router_password, router_not_config, network_id
from router_control_common import get_accesslist_tunnels, control_string

### Class router_control_telnet
class router_control_telnet:
    ### SET functions

    def set_tunnel(self, router_id, tunnel_id, address, mask, path):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            params = []
            ip_array = path.split(',')
            ip_dest = ip_array[len(ip_array)-1]
            ip_array[len(ip_array)-1] = ''
            ip_list = ' '.join(ip_array)
            params.update('tunnel_id', tunnel_id)
#            params.update('description', description)
            params.update('ip_dest', ip_dest)
            params.update('ip_list', ip_list)
            params.update('address', address)
            params.update('mask', mask)
            writer.write(control_string('SET_TUNNEL', params))
        asyncio.run(main())

    def set_accesslist(self, router_id, accesslist_id, protocol, address_in, mask_in, address_out, mask_out, tos):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            cfg_tos = ""
            int_tos = 0
            try:
                int_tos = int(tos)
            except:
                int_tos = 0
            if int_tos > 0:
                cfg_tos = " tos " + tos
            protocol_num = protocol
            if protocol_num == 'ICMP':
                protocol_num = '1'
            if protocol_num == 'TCP':
                protocol_num = '6'
            if protocol_num == 'UDP':
                protocol_num = '17'
            params = []
            params.update('accesslist_id', accesslist_id)
            params.update('protocol_num', protocol_num)
            params.update('address_in', address_in)
            params.update('mask_in', mask_in)
            params.update('address_out', address_out)
            params.update('mask_out', mask_out)
            params.update('cfg_tos', cfg_tos)
            writer.write(control_string('SET_ACCESSLIST', params))
        asyncio.run(main())

    def set_accesslist_tunnel(self, router_id, accesslist_id, ip_destiny):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            writer.write(control_string('SHOW_CONFIG', []))
            config = []
            response = ''
            while response != 'end':
                resp = await reader.readline()
                response = resp.strip()
                config.append(response)
            accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
            ip = ''
            seq = 0
            if len(accesslist_dict) > 0:
                accesslist = accesslist_dict.get(accesslist_id, None)
                if accesslist != None:
                    seq = accesslist['seq']
                if seq == 0:
                    for key, value in accesslist_dict.items():
                        if value['seq'] > seq:
                            seq = value['seq']
                    seq = seq + 10
            if seq == 0:
                seq = 10
            params = []
            params.update('seq', seq)
            params.update('accesslist_id', accesslist_id)
            params.update('ip_destiny', ip_destiny)
            writer.write(control_string('SET_ACCESSLIST_TUNNEL', params))
        asyncio.run(main())

    ### DEL functions

    def del_tunnel(self, router_id, tunnel_id):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            params['tunnel_id'] = tunnel_id
            writer.write(control_string('DEL_TUNNEL', params))
        asyncio.run(main())

    def del_accesslist(self, router_id, accesslist_id):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            writer.write(control_string('SHOW_CONFIG', []))
            config = []
            response = ''
            while response != 'end':
                resp = await reader.readline()
                response = resp.strip()
                config.append(response)
            accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
            accesslist = accesslist_dict.get(accesslist_id, None)
            params = []
            params.update('accesslist_id', accesslist_id)
            if accesslist != None:
                params.update('seq', accesslist['seq'])
                writer.write(control_string('DEL_SEQUENCE', params))
            writer.write(control_string('DEL_ACCESSLIST', params))
        asyncio.run(main())

    def del_accesslist_tunnel(self, router_id, accesslist_id):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            writer.write(control_string('SHOW_CONFIG', []))
            config = []
            response = ''
            while response != 'end':
                resp = await reader.readline()
                response = resp.strip()
                config.append(response)
            accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
            accesslist = accesslist_dict.get(accesslist_id, None)
            params = []
            params.update('accesslist_id', accesslist_id)
            if accesslist != None:
                params.update('seq', accesslist['seq'])
                writer.write(control_string('DEL_ACCESSLIST_TUNNEL', params))
        asyncio.run(main())

    ### LIST functions

    def list_tunnel(self, callback, client_queue, router_id):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            writer.write(control_string('SHOW_CONFIG', []))
            config = []
            response = ''
            while response != 'end':
                resp = await reader.readline()
                response = resp.strip()
                config.append(response)
            accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
            tunnel_list = [ f"list;tunnel;{router_id}" ]
            for tunnel_id, tunnel in tunnel_dict.items():
                tunnel_list.append(f"{tunnel_id},{tunnel['ip']},{tunnel['route']}")
            callback(client_queue, ';'.join(tunnel_list))
        asyncio.run(main())

    def list_router(self, callback, client_queue):
        list_txt = [ "list;router" ]
        router_list = get_router_list()
        if len(router_list) > 0:
            for key, value in router_list.items():
                router_txt = key + ',' + value['address'] + ':' + value['port']
                if value['user'] != None:
                    router_txt = router_txt + ',' + value['user']
                list_txt.append(router_txt)
        callback(client_queue, ';'.join(list_txt))

    def list_accesslist(self, callback, client_queue, router_id):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            writer.write(control_string('SHOW_CONFIG', []))
            config = []
            response = ''
            while response != 'end':
                resp = await reader.readline()
                response = resp.strip()
                config.append(response)
            accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
            access_txt = [ f"list;accesslist;{router_id}" ]
            for accesslist_id, accesslist in accesslist_dict.items():
                access_txt.append(f"{accesslist_id},{accesslist['seq']},{accesslist['ip']}")
            callback(client_queue, ';'.join(access_txt))
        asyncio.run(main())

    def list_accesstunnel(self, callback, client_queue, router_id, accesslist_id):
        async def main():
            if router_not_config(router_id):
                return
            tunnel_name = ''
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            writer.write(control_string('SHOW_CONFIG', []))
            config = []
            response = ''
            while response != 'end':
                resp = await reader.readline()
                response = resp.strip()
                config.append(response)
            accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
            accesslist = accesslist_dict.get(accesslist_id, None)
            if accesslist != None:
                for tunnel_id, tunnel in tunnel_dict.items():
                    tunnel_net = network_id(tunnel['ip'], tunnel['mask'])
                    accesslist_net = network_id(accesslist['ip'], tunnel['mask'])
                    if tunnel_net == accesslist_net:
                        tunnel_name = tunnel_id
            callback(client_queue, f"list;accesstunnel;{router_id};{accesslist_id};{tunnel_name}")
        asyncio.run(main())

    def list_tunnelaccess(self, callback, client_queue, router_id, tunnel_id):
        async def main():
            if router_not_config(router_id):
                return
            reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
            writer.write(control_string('SHOW_CONFIG', []))
            config = []
            response = ''
            while response != 'end':
                resp = await reader.readline()
                response = resp.strip()
                config.append(response)
            accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
            accesslist_list = [ f"list;tunnelaccess;{router_id};{tunnel_id}" ]
            tunnel = tunnel_dict.get(tunnel_id, None)
            if tunnel != None:
                for accesslist_id, accesslist in accesslist_dict.items():
                    tunnel_net = network_id(tunnel['ip'], tunnel['mask'])
                    accesslist_net = network_id(accesslist['ip'], tunnel['mask'])
                    if tunnel_net == accesslist_net:
                        accesslist_list.append(accesslist_id + ',' + accesslist['ip'])
            callback(client_queue, ';'.join(accesslist_list))
        asyncio.run(main())

