import sys
import os
import signal
import argparse
import logging
import time
from distutils.dir_util import copy_tree

from dir_sync.directory_monitor import DirectoryMonitor

OLD_FILES_STORAGE_NAME = '.ds'


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def prepare_directory(directory):
    '''Prepare directory to be tracked. Check if directory exists, if not
       create new directory. Create hidden .ds directory to store "old" copy
       of files, to have chance get differences on changes when it occures to
       transfer those changes to rempote soket.
    '''
    if not os.path.exists(directory) or not os.path.isdir(directory):
        os.mkdir(directory)
    old_files_storage = os.path.join(directory, OLD_FILES_STORAGE_NAME)
    copy_tree(directory, old_files_storage)


def main():
    logger = logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="dsyc-cl - client side application which can track the " +
                    "state of the directory and transfer changes to remote " +
                    "host to keep in sync remote directory"
    )
    parser.add_argument('-d',
                        help="path to directory which should be syncronised",
                        type=str)
    parser.add_argument('-h',
                        help="host to send changes on directory")
    parser.add_argument('-p',
                        help="port number")
    parser.add_argument('--polling_time', default=1,
                        help='time to retreive info about events in directory')
    args = parser.parse_args()

    directory = args.d
    host = args.h
    port = args.p
    polling_time = args.polling_time

    logger.info('dsync_cl starts...')
    prepare_directory(directory)
    excluded_dirs = [os.path.join(directory, OLD_FILES_STORAGE_NAME)]
    dm = DirectoryMonitor(directory, excluded_dirs)

    signal.signal(signal.SIGINT, signal_handler)
    interrupted = False
    while True:
        events = dm.get_events()

        time.sleep(polling_time)
        if interrupted:
            logger.info('dsync_cl finished...')
            break


if __name__ == "__main__":
    main()
