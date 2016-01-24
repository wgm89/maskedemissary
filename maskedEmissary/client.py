import socket
import select
import time

class Client(object):

    client_sock = None
    
    def __init__(self, client_sock):
        self.client_sock = client_sock

    
    
