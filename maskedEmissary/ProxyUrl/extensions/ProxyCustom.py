#custom your own proxy
from ProxyResourceAbs import ProxyResourceAbs

class ProxyCustom(ProxyResourceAbs):

    def run(self):

        return [
            {'url':'127.0.0.1:8118'}
        ]
    
