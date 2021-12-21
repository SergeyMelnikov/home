#!/usr/bin/env python

import datetime
import json
import sys
import urllib

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY


class AwairCollector(object):

    def __init__(self, ip):
        self.ip = ip
        self.device_config = json.loads(urllib.request.urlopen(f'http://{self.ip}/settings/config/data').read())
        print(self.device_config, flush=True)

    def collect(self):
        #        try:
        data = json.loads(urllib.request.urlopen(f'http://{self.ip}/air-data/latest').read())
        print(str(datetime.datetime.now()) + " " + str(data), flush=True)

        for metric, value in data.items():
            if metric in ['timestamp']:
                continue
            g = GaugeMetricFamily(
                'awair_sensor_' + metric,
                'Awair sensor data for ' + metric,
                labels=['device_uuid']
            )
            g.add_metric(value=value, labels=[self.device_config['device_uuid']])
            yield g


#        except Exception as e:
#            print(e)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 await_exporter.py <ip of Awair with local sensors enabled> "
              "[<port to export varz, default 8000>]")
        sys.exit(1)
    REGISTRY.register(AwairCollector(sys.argv[1]))
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = 8000

    start_http_server(port)

    import time

    while True:
        time.sleep(300)
