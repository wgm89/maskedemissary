# author by saeedwang
import sys
import socket
import urllib2 
import logging
import bs4
import re
import time
import base64
import thread
import gevent
from gevent import monkey
from gevent.pool import Pool

urllib2.socket.setdefaulttimeout(10)
monkey.patch_all()

from ProxyResourceAbs import ProxyResourceAbs

class CoolProxyNet(ProxyResourceAbs):

    url = "http://www.cool-proxy.net/proxies/http_proxy_list/sort:score/direction:desc"
    urls = {}
    poolsize = 10
    
    def __init__(self):
        self.pool = Pool(self.poolsize)
        
    def run(self):
        urls = []
        while 1:
            try:
                content = self._fetchUrl(self.url)  
                break
            except socket.timeout:
                time.sleep(5)
            
        soup = bs4.BeautifulSoup(content)
        total_page = soup.select(".next")[0].findPreviousSiblings("span")[0].find("a").get_text()
        total_page = int(total_page)
        
        url = self._build_url(1)
        self.getUrls(url)
        for page in xrange(1, total_page+1):
            url = self._build_url(page)
            self.pool.spawn(self.getUrls, url)
        self.join()
        return self._filter(self.urls).values()

    def getUrls(self, url):
        content = self._fetchUrl(url)
        soup = bs4.BeautifulSoup(content)
        for tr in soup.select("#main table tr")[1:-1]:
            tds = [td.get_text() for td in tr.find_all("td")]
            if len(tds) < 9:
                continue
            ip = self._parseIp(tds[0])
            if not ip:
                continue
            port = tds[1]
            country = tds[3]
            self.urls[ip] = {"url":ip+':'+port, "country":country}
    
    def join(self):
        self.pool.join()
        
    def _build_url(self, page):
        return "%s/page:%d" % (self.url, page)

    def _parseIp(self, script):
        m = re.search(r"\"(.*?)\"", script, re.M | re.I)
        if m:
            hashCode = m.group(1)
            hashCode = self.str_rot13(hashCode)
            ip = base64.decodestring(hashCode)
            return ip
        return False

    # if necessary
    def _filter(self, urls):
        if urls:
            for key, url in urls.items():
                if url['country'].lower() == '\x63\x68\x69\x6e\x61':
                    del urls[key]
        return urls

    def str_rot13(self, hashCode):
        return ''.join([s if not s.isalpha() else (chr(ord(s)+(13 if s.lower() < 'n' else -13))) for s in str(hashCode)])

if __name__ == '__main__':
    p = CoolProxyNet()
    print p.run()
