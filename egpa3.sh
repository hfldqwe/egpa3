#!/usr/bin/bash

# run-close egpa3 by time

`ps -ef|grep egpa3.py|awk '{print $2}'|xargs kill -9`

`cd /home/py/project/egpa3 && /home/py/.virtualenv/egpa/bin/python3.7 /home/py/project/egpa3/egpa3.py`
