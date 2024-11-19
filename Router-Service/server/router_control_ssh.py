#!/usr/bin/env python
import paramiko
from datetime import datetime
from topology import get_router_list, get_router_host, get_router_port, get_router_user, get_router_password, router_not_config, network_id
from router_control_common import get_accesslist_tunnels, control_string, list_router

### Class router_control_ssh
class router_control_ssh:
    def script(self, router_id, commands):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(get_router_host(router_id), port=get_router_port(router_id), username=get_router_user(router_id), password=get_router_password(router_id))
        stdin, stdout, stderr = ssh.exec_command("")
        index = 0
        timeout = True
        start = datetime.now()
        WAIT_QUIET_LINE = 1 # in seconds
        out_text = ""
        while not stdout.channel.exit_status_ready() and index <= len(commands):
            if stdout.channel.recv_ready():
                line = stdout.channel.recv(4096).decode("utf-8")
                out_text = out_text + line
                start = datetime.now()
            else:
                end = datetime.now()
                elapsed = (end - start).total_seconds()
                if elapsed > WAIT_QUIET_LINE:
                    timeout = True
                if timeout:
                    if index < len(commands):
                        stdin.channel.send(commands[index] + "\n")
                        timeout = False
                        start = datetime.now()
                    index = index + 1
        ssh.close()
        return(out_text)

    def get_config(self, router_id):
        output = self.script(router_id, control_string('SHOW_CONFIG', {}))
        config = []
        lines = output.split("\n")
        for response in lines:
            if response == 'end':
                break
            config.append(response.strip())
        return get_accesslist_tunnels(config)

    ### SET functions
    def set_tunnel(self, router_id, tunnel_id, address, mask, path, description = None):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        if description == None:
            description = tunnel_id
        params = {}
        ip_array = path.split(',')
        ip_dest = ip_array[len(ip_array)-1]
        ip_array[len(ip_array)-1] = ''
        ip_list = ' '.join(ip_array)
        params.update({'tunnel_id': tunnel_id})
        params.update({'description': description})
        params.update({'ip_dest': ip_dest})
        params.update({'ip_list': ip_list})
        params.update({'address': address})
        params.update({'mask': mask})
        self.script(router_id, control_string('SET_TUNNEL', params))

    def set_accesslist(self, router_id, accesslist_id, protocol, address_in, mask_in, address_out, mask_out, tos):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        cfg_tos = ""
        int_tos = 0
        try:
            int_tos = int(tos)
        except:
            int_tos = 0
        if int_tos > 0:
            cfg_tos = " tos " + tos
        protocol_num = protocol
        if protocol_num.upper() == 'ICMP':
            protocol_num = '1'
        if protocol_num.upper() == 'TCP':
            protocol_num = '6'
        if protocol_num.upper() == 'UDP':
            protocol_num = '17'
        params = {}
        params.update({'accesslist_id': accesslist_id})
        params.update({'protocol_num': protocol_num})
        params.update({'address_in': address_in})
        params.update({'mask_in': mask_in})
        params.update({'address_out': address_out})
        params.update({'mask_out': mask_out})
        params.update({'cfg_tos': cfg_tos})
        self.script(router_id, control_string('SET_ACCESSLIST', params))

    def set_accesslist_tunnel(self, router_id, accesslist_id, ip_destiny):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        accesslist_dict, tunnel_dict = self.get_config(router_id)
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
        params = {}
        params.update({'seq': seq})
        params.update({'accesslist_id': accesslist_id})
        params.update({'ip_destiny': ip_destiny})
        self.script(router_id, control_string('SET_ACCESSLIST_TUNNEL', params))

    ### DEL functions

    def del_tunnel(self, router_id, tunnel_id):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        params['tunnel_id'] = tunnel_id
        self.script(router_id, control_string('DEL_TUNNEL', params))

    def del_accesslist(self, router_id, accesslist_id):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        accesslist_dict, tunnel_dict = self.get_config(router_id)
        accesslist = accesslist_dict.get(accesslist_id, None)
        params = {}
        params.update({'accesslist_id': accesslist_id})
        if accesslist != None:
            params.update({'seq': accesslist['seq']})
            commands = control_string('DEL_SEQUENCE', params)
        commands = commands + control_string('DEL_ACCESSLIST', params)
        self.script(router_id, commands)

    def del_accesslist_tunnel(self, router_id, accesslist_id):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        accesslist_dict, tunnel_dict = self.get_config(router_id)
        accesslist = accesslist_dict.get(accesslist_id, None)
        params = {}
        params.update({'accesslist_id': accesslist_id})
        if accesslist != None:
            params.update({'seq': accesslist['seq']})
            self.script(router_id, control_string('DEL_ACCESSLIST_TUNNEL', params))

    ### LIST functions

    def list_tunnel(self, callback, client_queue, router_id):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        accesslist_dict, tunnel_dict = self.get_config(router_id)
        tunnel_list = [ f"list;tunnel;{router_id}" ]
        for tunnel_id, tunnel in tunnel_dict.items():
            tunnel_list.append(f"{tunnel_id},{tunnel['ip']},{tunnel['mask']},{tunnel['route']}")
        callback(client_queue, ';'.join(tunnel_list))

    def list_router(self, callback, client_queue):
        callback(client_queue, "list;router;" + list_router())

    def list_accesslist(self, callback, client_queue, router_id):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        accesslist_dict, tunnel_dict = self.get_config(router_id)
        access_txt = [ f"list;accesslist;{router_id}" ]
        for accesslist_id, accesslist in accesslist_dict.items():
            access_txt.append(f"{accesslist_id},{accesslist['seq']},{accesslist['ip']}")
        callback(client_queue, ';'.join(access_txt))

    def list_accesstunnel(self, callback, client_queue, router_id, accesslist_id):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        accesslist_dict, tunnel_dict = self.get_config(router_id)
        accesslist = accesslist_dict.get(accesslist_id, None)
        if accesslist != None:
            for tunnel_id, tunnel in tunnel_dict.items():
                tunnel_net = network_id(tunnel['ip'], tunnel['mask'])
                accesslist_net = network_id(accesslist['ip'], tunnel['mask'])
                if tunnel_net == accesslist_net:
                    tunnel_name = tunnel_id
        callback(client_queue, f"list;accesstunnel;{router_id};{accesslist_id};{tunnel_name}")

    def list_tunnelaccess(self, callback, client_queue, router_id, tunnel_id):
        if router_not_config(router_id) or get_router_user(router_id) == None:
            return
        accesslist_dict, tunnel_dict = self.get_config(router_id)
        accesslist_list = [ f"list;tunnelaccess;{router_id};{tunnel_id}" ]
        tunnel = tunnel_dict.get(tunnel_id, None)
        if tunnel != None:
            for accesslist_id, accesslist in accesslist_dict.items():
                tunnel_net = network_id(tunnel['ip'], tunnel['mask'])
                accesslist_net = network_id(accesslist['ip'], tunnel['mask'])
                if tunnel_net == accesslist_net:
                    accesslist_list.append(accesslist_id + ',' + accesslist['ip'])
        callback(client_queue, ';'.join(accesslist_list))
