#!/bin/bash

./googlehome_say.py 192.168.88.11 ru "$(curl -s http://192.168.88.15/air-data/latest | ./awair_status.py)"
