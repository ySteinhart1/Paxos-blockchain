import logging
import sys

import yaml

logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

port_mapping = {}

def configure(client_number: int):
    config = yaml.safe_load(open('config.yaml'))
    listening_port = config[client_number]
    logger.info('assigned port number %s', listening_port)
    for num, port in config.items():
        port_mapping[num] = port
    logger.debug('port mapping: %s', port_mapping)



def main(argv):
    if len(argv) == 1:
        logger.critical("No command line argument: missing client number")
        return
    configure(int(argv[1]))
    
if __name__ == "__main__":
    main(sys.argv)