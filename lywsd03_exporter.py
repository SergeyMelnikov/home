#!/usr/bin/env python
import datetime
import sys

import bluepy
import lywsd03mmc
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY


class Lywsd03Collector(object):

    def __init__(self, devices):
        self.devices = devices

    metrics = {}

    def collect(self):

        for device, m in self.metrics.items():
            for metric, value in m.items():
                g = GaugeMetricFamily(
                    'lywsd03_sensor_' + metric,
                    'Xiaomi Mijia LYWSD03 Bluetooth sensor data for ' + metric,
                    labels=['device_uuid']
                )
                g.add_metric(value=value, labels=[device])
                yield g

    def update(self):
        for device in self.devices:
            for attempt in range(10):
                try:
                    client = lywsd03mmc.Lywsd03mmcClient(device)
                    result = dict(client.data._asdict())
                    self.metrics[device] = result
                    log_record = {device: result}
                    print(f"{str(datetime.datetime.now())} {log_record}")
                    break
                except bluepy.btle.BTLEDisconnectError as e:
                    time.sleep(5)
                    pass
            else:
                print(f"Connection to {device} failed")
                self.metrics[device] = {}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 lywsd03_exporter.py <list of lywsd03 addresses> "
              "[<port to export varz, default 8000>]")
        sys.exit(1)
    collector = Lywsd03Collector(sys.argv[1].split(","))
    REGISTRY.register(collector)
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = 8002

    start_http_server(port)

    import time

    while True:
        collector.update()
        time.sleep(600)
