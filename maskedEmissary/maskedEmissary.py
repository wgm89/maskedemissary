from multiprocessing import Process  
import logging
from proxy import Proxy
from ProxyUrl import ProxyUrl

logging.basicConfig(level=logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S')

server = Proxy('', 9090)
proxyUrl = ProxyUrl()

Process(target=server.main_loop).start()
Process(target=proxyUrl.run).start()
