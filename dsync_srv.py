import sys
import os
import signal
import argparse

from receiver import SocketReceiver
from utils import create_logger


def main():
    logger = create_logger('server')
    parser = argparse.ArgumentParser(
        description="dsyc-srv - server application which can track the " +
                    "state of the remote directory and apply changes " +
                    "from remote host to keep in sync local directory"
    )
    parser.add_argument('-H', default='localhost',
                        help="host to send changes on directory")
    parser.add_argument('-p', default=6666,
                        help="port number")
    args = parser.parse_args()

    host = args.H
    port = args.p

    receiver = SocketReceiver(host, port)

    logger.info('dsync_srv starts...')

    while True:
        receiver.handle()

        logger.info('dsync_srv finishes...')


if __name__ == "__main__":
    main()
