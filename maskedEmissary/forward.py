import logging
import socket
import select
import utils
import time
import json

class Forward(object):

    forward_sock = None
    forward_to = None
    first_activity = None
    last_activity = None

    def __init__(self):
        self.first_activity = time.time()

    @utils.log
    def create_sock(self, forward_to):
        self.forward_to = forward_to
        ip, port = forward_to
        port = int(port)
        addrs = socket.getaddrinfo(ip, port, 0, socket.SOCK_STREAM, socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("getaddrinfo failed for %s:%d" % (ip, port))
        family, socktype, proto, _, _ = addrs[0]
        self.forward_sock = socket.socket(family, socktype, proto)
        self.forward_sock.settimeout(10)
        print self.forward_sock.getsockname()
    
class ForwardStorage(object):

    def __init__(self):
        self.comm = ForwardComm()

    @utils.log
    def get(self):
        forward = Forward()
        while 1:
            try:
                forward_url = self.forward_get()
                print "forward_url: %s", forward_url
                if not forward_url:
                    break
                forward_to = self._handle_url(forward_url)
                forward.create_sock(forward_to)
                start_time = time.time()
                forward.forward_sock.connect(forward_to)
            except socket.error:
                print("proxy connect faild")
                self.forward_remove(forward_url)
                continue
            forward.forward_sock.setblocking(0) #order is important
            use_time = time.time()-start_time
            self.forward_update_time(forward_url, use_time)
            print "response_time: %s" % use_time
            return forward
        raise Exception("not have valiable proxy")

    def forward_remove(self, forward_url):
        if isinstance(forward_url, Forward):
            forward_url = self._handle_forward(forward_url.forward_to)
        self.comm.send({"d":"remove", "forward":forward_url})

    def forward_update_time(self, forward_url, response_time):
        self.comm.send({"d":"update_time", "forward":forward_url, "response_time":response_time})

    def forward_get(self):
        return self.comm.send({"d":"get"})

    def error_page(self):
        pass

    def sweep(self, handles):
        for handle in handles.values():
            if isinstance(handle, Forward) and handle.first_activity and not handle.last_activity:
                if int(time.time() - handle.first_activity) > 5:
                    self.forward_remove(handle)

    def _handle_url(self, url):
        pos = url.rindex(':')
        return (url[0:pos], int(url[pos+1:]))

    def _handle_forward(self, forward):
        return "%s:%s" % (forward[0], str(forward[1]))

class ForwardComm(object):

    def send(self, msg):
        if not isinstance(msg, dict):
            return
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect("/tmp/emissary.sock")
        client.send(json.dumps(msg))
        msg = client.recv(1024)
        client.close()
        return msg


