#!/usr/bin/env python

import datetime
import json
import sys
import urllib

from types import SimpleNamespace
from pprint import pprint
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

lat = 59.94772
lon = 10.76756
altitude = 100
location = 'Nydalen'

class MetCollector(object):


    def collect(self):
        url=f'https://api.met.no/weatherapi/nowcast/2.0/complete?lat={lat}&lon={lon}&altitude={altitude}'
        response = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'melnikov home display sergey@melnikov.no'})).read())
        data = response['properties']['timeseries'][0]['data']['instant']['details']
        print(str(datetime.datetime.now()) + " " + str(data), flush=True)
        for metric, value in data.items():
            g = GaugeMetricFamily(
                'met_no_' + metric,
                'met.no data for ' + metric,
                labels=['lat','lon','altitude', 'location']
            )
            g.add_metric(value=value, labels=[str(lat), str(lon), str(altitude), location])
            #print(g)
            yield g
#      except Exception as e:
#        print(e)
#      else:
#        print("ok")

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Usage: python3 met.no_exporter.py [<port to export varz, default 8000>]")
        sys.exit(1)
    REGISTRY.register(MetCollector())
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8012

    start_http_server(port)

    import time

    while True:
        time.sleep(300)
