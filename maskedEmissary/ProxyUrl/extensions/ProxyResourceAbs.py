import urllib2
import logging

class ProxyResourceAbs(object):
    
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(ProxyResourceAbs, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def run(self):
        raise Exception("run")

    def _fetchUrl(self, url):
        try:
            response = urllib2.urlopen(url, timeout=5)
            logging.info("%s start get url" % url)
        except urllib2.URLError, e:
            logging.error("%s connect faild" % url)
        return response.read()
    
