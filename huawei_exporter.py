#!/usr/bin/python3
import datetime
import sys

from huawei_lte_api.ApiGroup import ApiGroup
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.Client import Client
from huawei_lte_api.Connection import GetResponseType
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client.metrics_core import CounterMetricFamily, InfoMetricFamily


class DevInfo2(ApiGroup):
    def config(self) -> GetResponseType:
        return self._connection.get(
            'deviceinformation/dev_info.xml', prefix='config')


class HuaweiCollector(object):
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password

    def collect(self):
        connection = AuthorizedConnection(self.ip, self.username, self.password)
        client = Client(connection)

        monitoring_status = client.monitoring.status()
        network_type = int(monitoring_status['CurrentNetworkTypeEx'])
        network_types = dict()
        for e in client.config_global.net_type()['config']['networktypes']:
            network_types[int(e['index'], 10)] = e['networktype']

        if network_type:
            network_type = network_types[network_type]
        else:
            network_type = 'No connection'

        stat = dict()
        current_plmn = client.net.current_plmn()

        stat['operator'] = current_plmn["FullName"]
        stat['network_type'] = network_type
        stat['signal'] = monitoring_status["SignalIcon"]
        yield GaugeMetricFamily(
            'modem_signal',
            'Modem signal level from 1 to 5',
            value=stat['signal']
        )
        device_information = client.device.information()
        device_information2 = DevInfo2(connection).config()['config']
        stat['temperature'] = int(device_information2['chiptemp']) / 10.0
        yield GaugeMetricFamily(
            'modem_temperature',
            'Modem temperature',
            value=stat['temperature'],
            unit="degrees_celsius"
        )
        stat['serial_number'] = device_information['SerialNumber']
        stat['device'] = device_information2['DeviceName']
        traffic_statistics = client.monitoring.traffic_statistics()
        stat['total_upload'] = traffic_statistics['TotalUpload']
        yield CounterMetricFamily(
            'modem_upload_total',
            'Total upload from modem reset in bytes',
            value=stat['total_upload'],
            unit="bytes"
        )
        stat['total_download'] = traffic_statistics['TotalDownload']
        yield CounterMetricFamily(
            'modem_download_total',
            'Total download from modem reset in bytes',
            value=stat['total_download'],
            unit="bytes"
        )
        device_signal = client.device.signal()

        for i in ['rssi', 'rsrp', 'rsrq', 'sinr', 'cell_id']:
            stat[i] = device_signal[i]

        yield InfoMetricFamily(
            'modem_connection',
            'Properties of connection',
            value={'operator': stat['operator'], 'network_type': stat['network_type'], 'cell_id': stat['cell_id']},
        )

        yield GaugeMetricFamily(
            'modem_rssi',
            'Modem RSSI',
            value=stat['rssi'][:-3],
            unit="dBm"
        )
        yield GaugeMetricFamily(
            'modem_rsrp',
            'Modem RSRP',
            value=stat['rsrp'][:-3],
            unit="dBm"
        )
        yield GaugeMetricFamily(
            'modem_rsrq',
            'Modem RSRQ',
            value=stat['rsrq'][:-2],
            unit="dB"
        )
        yield GaugeMetricFamily(
            'modem_sinr',
            'Modem SINR',
            value=stat['sinr'][:-2],
            unit="dB"
        )

        # print('monitoring_status = ', monitoring_status)
        # print('current_plmn = ', current_plmn)
        # print('device_information = ', device_information)
        # print('traffic_statistics = ', traffic_statistics)
        # print('device_information2 = ', device_information2)
        print(str(datetime.datetime.now()) + " " + str(stat), flush=True)
        # return stat


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 huawei_exporter.py <ip> <user> <password> [<port to export varz, default 8001>]")
        sys.exit(1)

    REGISTRY.register(HuaweiCollector('http://' + sys.argv[1], sys.argv[2], sys.argv[3]))
    if len(sys.argv) > 4:
        port = int(sys.argv[4])
    else:
        port = 8001

    start_http_server(port)

    import time

    while True:
        time.sleep(300)
