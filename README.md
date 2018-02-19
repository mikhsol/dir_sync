# DIR_SYNC

Simple dropbox-like application which allow you to monitor changes of folder,
files which stored in this folder and nested folders.

Application was created and tested on Ubuntu 17.10. It does not support all editors. Works fine with command line tool like echo and Visual Studio Code. Problem appears with Vim editor, according it way to file modifications.

# Setup

* Create virtualenv inside project folder:
  * `virtualenv -p /usr/bin/python3 evn_dir_sync`
  * `source env_dir_sync/bin/activate`
  * `pip install -r requirements.txt`

* Deactivate virtualenv:
  * `deactivate`

___

# Running

* Start the sever first:
  * `python dsync_srv.py` - will run the server with default settings
  * `python dsync_srv.py -h` - will show help message

* Start the client:
  * `python dsync_cl.py -d folder_name` - `-d` flag responsible for tracking
    directory name, it is compulsory one
  * `python dsync_cl.py -h` - will show help message

___

# Testing

* Testing without coverage:
  * `pytest`

* Testing with coverage:
  * `pytest --cov-report=html --cov=directory_monitor --cov=event_processor --cov=files_comporator --cov=receiver --cov=sender --cov=utils`

___
