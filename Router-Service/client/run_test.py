from freertr_polka import freertr_polka

freertr = freertr_polka()
freertr.router_set('VIT0071', '10.160.0.20', '22222', 'rare', 'rare')
freertr.tunnel_set('VIT0071', 'tunnel174516', '40.17.16.1', '255.255.255.252', '10.45.45.45,10.16.16.16', 'POLKA tunnel from VIT0071[1] -> SPO0021[2] via MG')
freertr.accesslist_set('VIT0071', 'tunnel_vix_sp', 'tcp', '10.0.0.0', '255.255.255.0', '10.16.0.0', '255.255.255.0', '0x20')
freertr.accesslist_assign('VIT0071', 'tunnel_vix_sp', '40.17.16.1')
freertr.close()
