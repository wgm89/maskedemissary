# -*- coding: utf-8 -*- 
from __future__ import absolute_import, division, print_function, \
        with_statement

import sys
import urllib2
import logging
import bs4
import re
from ProxyResourceAbs import ProxyResourceAbs

class ProxyCom(ProxyResourceAbs):

    url = "http://www.proxy.com.ru/"

    def __init__(self):
        proxy_handler = urllib2.ProxyHandler({"http" : 'http://127.0.0.1:8118'})
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)

    def run(self):
        urls = []
        content = self._fetchUrl(proxyStorageUrl)
        content = unicode(content, "gb2312").encode("utf8")
        m = re.search(r"共(\d+)页", content, re.M | re.I)
        if m:
            total_page = int(m.group(1))
        else:
            total_page = 1
        for page in range(1, total_page+1):
            print ("%slist_%s.html" % (self.url, page))
            urls.extend(self.getUrls("%slist_%s.html" % (self.url, page)))
        return urls

    def getUrls(self, url):
        content = self._fetchUrl(url)
        soup = bs4.BeautifulSoup(content)
        urls = [(tr.find_all("td")[1].get_text(), tr.find_all("td")[2].get_text(), tr.find_all("td")[3].get_text())
                for tr in soup.select("body font table td")[0].findNextSiblings("td")[0].find("table").select("tr")[1:]]
        return urls


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO,
            format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    proxy = proxyCom()
    urls = proxy.run()
    print(urls)
