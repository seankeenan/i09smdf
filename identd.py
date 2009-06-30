#!/usr/bin/env python
import socket
import time
import threading

class Identd(threading.Thread):
    def __init__(self, username):
        threading.Thread.__init__(self)
        self.username = username
        
    def run(self):
        ident = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        ident.bind((socket.gethostname(), 113))
        ident.listen(1)
        #accept connections from outside
        (cs, address) = ident.accept()
        msg = cs.recv(512)
        (serverport, clientport) = map(int,msg.split(" , "))
        response = "%d, %d : USERID : %s : %s \r\n" % (serverport, clientport,
                                                self.username, self.username)
        cs.sendall(response)