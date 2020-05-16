import logging
import sys

import yaml


logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def configure(client_number: int):
    config = yaml.safe_load(open('config.yaml'))
    # using f-strings
    client_name = f'client_{client_number}_port'
    listening_port = config[client_name]
    logger.info('assigned port number %s', listening_port)

def main(argv):

    if len(argv) == 1:
        logger.critical("No command line argument: missing client number")
        return
    configure(int(argv[1]))
    
if __name__ == "__main__":
    main(sys.argv)