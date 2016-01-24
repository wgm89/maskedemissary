# -*- coding: utf-8 -*- 
import json
import os
import socket
import threading
import time
import Queue
from collections import deque

ProxyUrlConf = json.load(file(os.path.join(os.path.dirname(__file__), "ProxyUrl.conf")))
urlModule = ProxyUrlConf['modules']
interval_time = int(ProxyUrlConf['interval_time'])

class ProxyUrl(object):

    pUrls = dict()

    def __call__(self):
        pass

    def run(self):
        self._bgWorker()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists("/tmp/emissary.sock"):
            os.unlink("/tmp/emissary.sock")
        server.bind("/tmp/emissary.sock")
        server.listen(0)
        while True:
            connection, address = server.accept()
            msg = connection.recv(1024)
            print msg
            res = self._handle_msg(msg)
            if not res:
                res = ''
            connection.send(res)
            connection.close()

    def getOne(self):
        pUrls = sorted(self.pUrls.items(), key=lambda x : x[1]["response_time"])
        try:
            url = pUrls[0][0]
        except IndexError:
            return
        #pos = url.rindex(':')
        forward = url
        return forward

    def update_time(self, forward, response_time):
        url = ':'.join(map(lambda i: str(i), list(forward)))
        if self.pUrls.has_key(url):
            self.pUrls[url]["response_time"] = response_time

    def remove(self, forward):
        if self.pUrls.has_key(forward):
            del self.pUrls[forward]
        print 'remove'

    def _bgWorker(self):
        scr = Scrabble('scr', self.pUrls)
        scr.setDaemon(True)
        scr.start()

    def _handle_msg(self, msg):
        if not msg:
            return
        try:
            msg = json.loads(msg)
        except:
            return
        if not isinstance(msg, dict):
            return
        if msg['d'] == 'get':
            return self.getOne()
        elif msg['d'] == 'update_time':
            return self.update_time(msg['forward'], msg['response_time'])
        elif msg['d'] == 'remove':
            return self.remove(msg['forward'])
        return

class Scrabble(threading.Thread):

    pUrls = None

    def __init__(self, threadname, pUrls):
        threading.Thread.__init__(self,name=threadname)
        self.pUrls = pUrls

    def run(self):
        while 1:
            for module in urlModule:
                source_module = __import__("ProxyUrl.extensions.%s" % module, fromlist=module)
                urls = getattr(source_module, module)().run()
                if urls and isinstance(urls, list):
                    self._load(urls)
            #todo
            for url in self.pUrls.keys():
                self._get_ack_time(url)
            
            time.sleep(interval_time)
       
    def _load(self, urls):
        for url_detail in urls:
            url = url_detail['url'].strip('/ ')
            self.pUrls[url] = {"url":url, "response_time":10000}
    
    def _get_ack_time(self, url):

        try:
            start_time = time.time()
            ip, port = url.split(":")
            port = int(port)
            addrs = socket.getaddrinfo(ip, port, 0, socket.SOCK_STREAM, socket.SOL_TCP)
            if len(addrs) == 0:
                raise Exception("getaddrinfo failed for %s:%d" % (ip, port))
            family, socktype, proto, _, _ = addrs[0]
            s = socket.socket(family, socktype, proto)
            s.connect((ip, port))
            use_time = time.time()-start_time
            self.pUrls[url]['response_time'] = use_time
        except socket.error:
            print "del"
            del self.pUrls[url]

if __name__ == '__main__':
    p = ProxyUrl()
    p.run()
