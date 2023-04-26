#!/usr/bin/env python

import datetime
import json
import sys
import urllib

from pprint import pprint
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY



class Awair:
    def __init__(self, ip, name, model):
        self.ip = ip
        self.name = name
        self.model = model


config = [
    Awair("192.168.93.11", "Bedroom", "awair-r2"),
    Awair("192.168.93.10", "Office", "awair-element"),
]


class AwairCollector(object):

    def __init__(self, config):
        self.devices = config
        for device in self.devices:
            device.device_config = json.loads(urllib.request.urlopen(f'http://{device.ip}/settings/config/data').read())
            pprint(device.device_config)

    def collect(self):
#      try:
        for device in self.devices:
            data = json.loads(urllib.request.urlopen(f'http://{device.ip}/air-data/latest').read())
            print(str(datetime.datetime.now()) + " " + str(data), flush=True)

            for metric, value in data.items():
                if metric in ['timestamp']:
                    continue
                g = GaugeMetricFamily(
                    'awair_sensor_' + metric,
                    'Awair sensor data for ' + metric,
                    labels=['device_uuid']
                )
                g.add_metric(value=value, labels=[device.device_config['device_uuid']])
                #print(g)
                yield g
                NEW_NAME = {
                    'temp': 'temperature',
                    'humid': 'humidity'
                }
                metric = NEW_NAME.get(metric, metric)
                g = GaugeMetricFamily(
                    'sensor_' + metric,
                    'sensor data for ' + metric,
                    labels=['device_uuid', 'device_name', 'device_type']
                )
                g.add_metric(value=value, labels=[device.device_config['device_uuid'], device.name, device.model])
                #print(g)
                yield g
#      except Exception as e:
#        print(e)
#      else:
#        print("ok")

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Usage: python3 await_exporter.py [<port to export varz, default 8000>]")
        sys.exit(1)
    REGISTRY.register(AwairCollector(config))
    if len(sys.argv) > 1:
        port = int(sys.argv[2])
    else:
        port = 8000

    start_http_server(port)

    import time

    while True:
        time.sleep(300)
