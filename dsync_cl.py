import sys
import os
import argparse
import logging
import time
from distutils.dir_util import copy_tree

from directory_monitor import DirectoryMonitor
from event_processor import ClientEventProcessor
from sender import SocketSender
from utils import create_logger

OLD_FILES_STORAGE_NAME = '.ds'

logger = create_logger('client')


def prepare_directory(directory):
    '''Prepare directory to be tracked. Check if directory exists, if not
       create new directory. Create hidden .ds directory to store "old" copy
       of files, to have chance get differences on changes when it occures to
       transfer those changes to rempote soket.
    '''
    if not os.path.exists(directory) or not os.path.isdir(directory):
        os.mkdir(directory)
    old_files_storage = os.path.join(directory, OLD_FILES_STORAGE_NAME)
    if os.path.exists(old_files_storage):
        os.system('rm -r {}'.format(old_files_storage))
    copy_tree(directory, old_files_storage)


def main():
    parser = argparse.ArgumentParser(
        description="dsyc-cl - client side application which can track the " +
                    "state of the directory and transfer changes to remote " +
                    "host to keep in sync remote directory"
    )
    parser.add_argument('-d',
                        help="path to directory which should be syncronised",
                        type=str, required=True)
    parser.add_argument('-H', default='localhost',
                        help="host to send changes on directory")
    parser.add_argument('-p', default=6666,
                        help="port number")
    parser.add_argument('--polling_time', default=1,
                        help='time to retreive info about events in directory')
    args = parser.parse_args()

    directory = args.d
    host = args.H
    port = args.p
    polling_time = args.polling_time

    logger.info('dsync_cl starts...')
    prepare_directory(directory)
    excluded_dirs = [os.path.join(directory, OLD_FILES_STORAGE_NAME)]
    dm = DirectoryMonitor(directory, excluded_dirs)
    sender = SocketSender(host, port, excluded_dirs)
    sender.init(directory)
    ep = ClientEventProcessor(directory, sender)

    while True:
        events = dm.get_events()

        for event in events:
            ep.process(event)

        time.sleep(polling_time)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info('dsync_cl stops...')
