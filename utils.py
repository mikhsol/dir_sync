import logging


def create_logger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s' +
                                  ' - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    return logger


class SocketEvents:
    FILE = b'FILE'
    DIRECTORY = b'DIRECTORY'
    EVENT = b'EVENT'
    READY = b'READY'
    OK = b'OK'
    INIT = b'INIT'
    FINISHED = b'FINISHED'
