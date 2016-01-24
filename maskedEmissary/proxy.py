import socket
import select
import time
import sys
import logging
import Queue
import utils
from lru import LRUCacheSock
from forward import ForwardStorage
from client import Client 
import re

##todo
##signal on over

MAX_RECEIVE_SIZE = 1024
MAX_CLIENTS_NUM	 = 2048
EPOLL_TIMEOUT = 1

forwardStorage = ForwardStorage()

class Proxy(object):

    fd_to_socket = {}
    request_msg = {}
    _fd_to_handle = {}

    def __init__(self, host, port):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((host, port))
        self.server_sock.listen(MAX_CLIENTS_NUM)
        self.server_sock.setblocking(0)
        self.server_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.start_time = time.time()
        self.last_activity = self.start_time
        self.cache = LRUCacheSock(timeout=300, close_callback=self._on_close)
        self._epoll = select.epoll()
        self._epoll.register(self.server_sock, select.EPOLLIN | select.EPOLLERR)
        self.fd_to_socket[self.server_sock.fileno()] = self.server_sock

    def main_loop(self):
        while 1:
            events = self._epoll.poll(EPOLL_TIMEOUT)
            if int(time.time()) % 3 == 0:
                forwardStorage.sweep(self._fd_to_handle)
            if not events:
                continue
            for fd, event in events:
                sock = self.fd_to_socket.get(fd)
                if sock == self.server_sock:
                    if event & select.EPOLLERR:
                        raise Exception("epoll error")
                    self.on_accept()
                else:
                    if self._fd_to_handle.has_key(fd) and hasattr(self._fd_to_handle[fd], 'last_activity'):
                        self._fd_to_handle[fd].last_activity = time.time()
                    if event & select.EPOLLERR:
                        self._on_close(sock)
                    if event & select.EPOLLIN:
                        self.on_recv(sock)
                    if event & select.EPOLLOUT:
                        self.on_send(sock)
                    if event & (select.EPOLLHUP | select.EPOLLERR):
                        self._on_close(sock)

    @utils.log
    def on_accept(self):
        forwardHandle = forwardStorage.get()
        forward_sock = forwardHandle.forward_sock
        forward_fd = forward_sock.fileno()
        self._fd_to_handle[forward_fd] = forwardHandle
        
        client_sock, client_addr = self.server_sock.accept()
        client_fd = client_sock.fileno()
        self._fd_to_handle[client_fd] = Client(client_sock)
        client_sock.setblocking(0)
        client_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        if forward_sock and client_sock:
            logging.info("client %s accept" % ':'.join([str(i) for i in list(client_addr)]))
            self._epoll.register(forward_sock, select.EPOLLIN | select.EPOLLERR)
            self._epoll.register(client_sock, select.EPOLLIN | select.EPOLLERR)
            self.cache[client_sock] = forward_sock
            self.cache[forward_sock] = client_sock
            self.fd_to_socket[forward_fd] = forward_sock
            self.fd_to_socket[client_fd] = client_sock
            self.request_msg[forward_fd] = ""
            self.request_msg[client_fd] = ""
        else:
            logging.info("Can't establish connection with remote server.")
            logging.info("Closing connection with client side %s" % clientaddr)
            client_sock.close()
        if self._is_timeout:
            self.cache.sweep()
        self.last_activity = time.time()

    @utils.log
    def on_recv(self, client_sock):
        if not client_sock:
            return
        try:
            msg = client_sock.recv(MAX_RECEIVE_SIZE)
        except socket.error:
            self._on_close(client_sock)
            forwardStorage.forward_remove(self._fd_to_handle[client_sock.fileno()])
            return
        if msg:
            self.request_msg[client_sock.fileno()] += msg 
        msg = self.request_msg[client_sock.fileno()] 
        if msg:
            s_l = self.cache[client_sock].send(msg)
            self.request_msg[client_sock.fileno()] = msg[s_l:]
            if s_l < len(msg):
                self._epoll.modify(client_sock.fileno(), select.EPOLLOUT)
        else:
            self._on_close(client_sock)

    @utils.log
    def on_send(self, client_sock):
        try:
            msg = self.request_msg[client_sock.fileno()]
            s_l = self.cache[client_sock].send(msg)
            self.request_msg[client_sock.fileno()] = msg[s_l:]
            if not self.request_msg[client_sock.fileno()]:
                self._epoll.modify(client_sock.fileno(), select.EPOLLIN | select.EPOLLERR)
        except socket.error:
            self._on_close(client_sock)
            return

    @utils.log
    def _on_close(self, s):
        try:
            logging.info("%s disconnect")
            self._epoll.unregister(s)
            self._epoll.unregister(self.cache[s])
            del self.fd_to_socket[self.cache[s].fileno()]
            del self.fd_to_socket[s.fileno()]

            del self._fd_to_handle[self.cache[s].fileno()]
            del self._fd_to_handle[s.fileno()]

            self.cache[s].close()
            s.close()
        except socket.error:
            logging.info("socket disconnected already")

    @property
    def _is_timeout(self):
        return (time.time() - self.last_activity) > 60

if __name__ == '__main__':
    server = Proxy('', 9090)
    print("listen 9090")
    try:
        server.main_loop()
    except KeyboardInterrupt:
        logging.info("Ctrl C - Stopping server")
        sys.exit(1)
