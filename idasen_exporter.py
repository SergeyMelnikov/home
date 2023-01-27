#!/usr/bin/env python

import datetime
import json
import re
import subprocess
import sys
import urllib

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY


class IdasenCollector(object):

    def collect(self):
        output = str(subprocess.check_output(["idasen-controller", "--server-address", "192.168.93.2", "--forward", "--watch"]))
        height = int(re.findall("\d+", output)[0])
        print(str(datetime.datetime.now()) + " " + str(height), flush=True)
        g = GaugeMetricFamily(
            'table_height',
            'Table Height',
            labels=['device_uuid', 'device_name', 'device_type']
        )
        g.add_metric(value=height, labels=['C5:AB:F2:D5:82:81', 'Office', 'IKEA IDÅSEN'])
        yield g

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Usage: python3 idasen_exporter.py [<port to export varz, default 8011>]")
        sys.exit(1)
    REGISTRY.register(IdasenCollector())
    if len(sys.argv) > 2:
        port = int(sys.argv[1])
    else:
        port = 8011

    start_http_server(port)

    import time

    while True:
        time.sleep(300)
