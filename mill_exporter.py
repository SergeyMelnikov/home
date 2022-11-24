#!/usr/bin/env python

import datetime
import json
import sys
import urllib

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY


class MillCollector(object):

    def __init__(self, ip):
        self.ip = ip

    def collect(self):
        for i in range(10):
            try:
                data = json.loads(urllib.request.urlopen(f'http://{self.ip}/control-status', timeout=5).read())
                break
            except Exception as e:
                print(e)
                time.sleep(5)
                print(f"Reconnecting, try {i}/10")
                continue
        else:
            return
        #open_window = json.loads(urllib.request.urlopen(f'http://{self.ip}/open-window').read())
        #data = {**control_status, **open_window}
        print(str(datetime.datetime.now()) + " " + str(data), flush=True)
        metrics = {
            'ambient_temperature': 'the temperature measured by sensor in Celsius degrees (with calibration offset value included)',
            'current_power': 'the current heating power in Watts',
            'control_signal': 'the control signal of the PID regulator (0-100%)',
            'raw_ambient_temperature': 'the temperature measured by sensor in Celsius degrees without calibration offset value',
            'set_temperature': 'the current set temperature in Celsius degrees',
            'open_window_active_now': 'the open widows status: -1 - Disabled not active now, 0 - Enabled not active now, 1 - Enabled active now, -10 - error',
        }
        for metric in metrics.keys():
            if metric not in data:
                print(f"No {metric} in data")
                continue
            value = data[metric]
            if metric == 'open_window_active_now':
                mapping = {
                    "Disabled not active now": -1,
                    "Enabled not active now": 0,
                    "Enabled active now": 1,
                }
                value = mapping.get(value, -10)
            g = GaugeMetricFamily(
                'heater_' + metric,
                metrics[metric],
                labels=['device_uuid', 'device_name', 'device_type']
            )
            g.add_metric(value=value, labels=['70:b8:f6:b7:f4:78', 'Bedroom', 'Mill-OIL1500WIFI3'])
            yield g

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 mill_exporter.py <ip of Mill Heater with local API enabled> "
              "[<port to export varz, default 8001>]")
        sys.exit(1)
    REGISTRY.register(MillCollector(sys.argv[1]))
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = 8010

    start_http_server(port)

    import time

    while True:
        time.sleep(300)
