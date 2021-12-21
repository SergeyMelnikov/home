#!/bin/bash

./googlehome_say.py 192.168.99.5 ru "$(curl -s http://awair/air-data/latest | ./awair_status.py)"
