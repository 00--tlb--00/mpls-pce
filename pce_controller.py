__author__ = 'dipsingh'

import socket
import gevent
import pcep_handler
import te_controller
import json
from gevent import monkey
monkey.patch_socket()

MAXCLIENTS = 10
PCEADDR='0.0.0.0'
PCEPORT=4189
ERO_LIST = ('172.16.2.2','172.16.3.3','172.16.4.4') # ERO List
TUNNEL_SRC_DST = ('1.1.1.1','4.4.4.4')  #Tunnel Source and Destination
LSPA_PROPERTIES = (7,7,0) #Setup Priority,Hold Priority,Local Protection Desired(0 means false)
TUNNEL_NAME = b'XRV1_t1'


def send_ka(client_sock,pcep_context):
    while True:
        client_sock.send(pcep_context.generate_ka_msg())
        gevent.sleep(pcep_context._ka_timer)

def pcc_handler(client_sock,sid,controller):
    Flag=True
    pcep_context = pcep_handler.PCEP(open_sid = sid)
    print ("Received Client Request from ",client_sock[1])
    msg_received = client_sock[0].recv(1000)
    pcep_context.parse_recvd_msg(msg_received)
    client_sock[0].send(pcep_context.generate_open_msg(30))
    ka_greenlet = gevent.spawn(send_ka,client_sock[0],pcep_context)
    while True:
        msg= client_sock[0].recv(1000)
        parsed_msg = pcep_context.parse_recvd_msg(msg)
        result = controller.handle_pce_message(client_sock[1],parsed_msg)
        pcep_msg= None
        if Flag:
            pcep_msg = pcep_context.generate_lsp_inititate_msg(ERO_LIST,TUNNEL_SRC_DST,LSPA_PROPERTIES,TUNNEL_NAME)
            print ("Creating TE Tunnel")
            Flag=False
        if pcep_msg:
            client_sock[0].send(pcep_msg)
    client_sock[0].close()

def main ():
    CURRENT_SID=0
    pce_server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    controller = te_controller.TEController()
    pce_server_sock.bind((PCEADDR,PCEPORT))
    pce_server_sock.listen(MAXCLIENTS)
    while True:
        client = pce_server_sock.accept()
        gevent.spawn(pcc_handler,client,CURRENT_SID,controller)
        CURRENT_SID += 1

if __name__ == '__main__':
    main()
