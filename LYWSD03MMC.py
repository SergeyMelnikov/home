# Based on https://github.com/JsBergbau/MiTemperature2

import os
import signal
import threading
import time
import traceback
from collections import deque
from dataclasses import dataclass

import bluetooth._bluetooth as bluez
from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway

from bluetooth_utils import (toggle_device,
                             enable_le_scan, parse_le_advertising_events,
                             disable_le_scan, raw_packet_to_str)

SENSORS = {
    'A4:C1:38:CE:9B:6D': 'Living Room',
    'A4:C1:38:84:28:3E': 'Bathroom',
}
DEV_ID = 0  # the bluetooth device is hci0
WATCHDOG_TIMER = 300  # Re-enable scanning after not receiving any BLE packet after X seconds


@dataclass
class Measurement:
    temperature: float
    humidity: int
    voltage: float
    battery: int = 0
    timestamp: int = 0
    sensorname: str = ""
    mac: str = ""
    rssi: int = 0


measurements = deque()


def signal_handler(sig, frame):
    disable_le_scan(sock)
    os._exit(0)


def push_to_prometheus(measurement: Measurement):
    PROMETHEUS_URL = "http://localhost:9091"

    registry = CollectorRegistry()

    for metric in ["temperature", "humidity", "voltage", "battery", "rssi"]:
        t = Gauge('sensor_' + metric, 'sensor data for ' + metric, registry=registry)
        t.set(getattr(measurement, metric))
    pushadd_to_gateway(PROMETHEUS_URL, job='pushgateway',
                       grouping_key={'device_uuid': measurement.mac, 'device_name': measurement.sensorname,
                                     'device_type': 'lywsd03mmc'},
                       registry=registry)


def thread_SendingData():
    global measurements

    while True:
        try:
            measurement = measurements.popleft()
            # print("Pushing:", measurement)
            push_to_prometheus(measurement)

        except IndexError:
            # print("No Data")
            time.sleep(1)
        except Exception as e:
            print(e)
            print(traceback.format_exc())


sock = None  # from ATC
lastBLEPacketReceived = 0
BLERestartCounter = 1


def keepingLEScanRunning():  # LE-Scanning gets disabled sometimes, especially if you have a lot of BLE connections, this thread periodically enables BLE scanning again
    global BLERestartCounter
    while True:
        time.sleep(1)
        now = time.time()
        if now - lastBLEPacketReceived > WATCHDOG_TIMER:
            print("Watchdog: Did not receive any BLE packet within", int(now - lastBLEPacketReceived),
                  "s. Restarting BLE scan. Count:", BLERestartCounter)
            disable_le_scan(sock)
            enable_le_scan(sock, filter_duplicates=False)
            BLERestartCounter += 1
            print("")
            time.sleep(5)  # give some time to take effect


# Main loop --------

dataThread = threading.Thread(target=thread_SendingData)
dataThread.start()

signal.signal(signal.SIGINT, signal_handler)

advCounter = dict()

toggle_device(DEV_ID, True)

try:
    sock = bluez.hci_open_dev(DEV_ID)
except:
    print("Error: cannot open bluetooth device %i" % DEV_ID)
    raise

enable_le_scan(sock, filter_duplicates=False)

try:
    def decode_data_pvvx(mac, adv_type, data_str, rssi):
        preeamble = "161a18"
        packetStart = data_str.find(preeamble)
        offset = packetStart + len(preeamble)
        strippedData_str = data_str[offset:]
        dataIdentifier = data_str[(offset - 4):offset].upper()

        if dataIdentifier == "1A18" and mac in SENSORS and len(strippedData_str) == 30:
            advNumber = strippedData_str[-4:-2]
            if advCounter.get(mac, None) != advNumber:
                print("BLE packet - Custom: %s %02x %s %d" % (mac, adv_type, data_str, rssi))
                advCounter[mac] = advNumber
                return Measurement(
                    battery=int.from_bytes(bytearray.fromhex(strippedData_str[24:26]), byteorder='little',
                                           signed=False),
                    humidity=int.from_bytes(bytearray.fromhex(strippedData_str[16:20]), byteorder='little',
                                            signed=False) / 100.,
                    temperature=int.from_bytes(bytearray.fromhex(strippedData_str[12:16]), byteorder='little',
                                               signed=True) / 100,
                    voltage=int.from_bytes(bytearray.fromhex(strippedData_str[20:24]), byteorder='little',
                                           signed=False) / 1000.,
                    rssi=rssi,
                    timestamp=int(time.time()),
                    mac=mac,
                    sensorname=SENSORS[mac] if mac in SENSORS else mac
                )


    def le_advertise_packet_handler(mac, adv_type, data, rssi):
        global lastBLEPacketReceived
        lastBLEPacketReceived = time.time()
        data_str = raw_packet_to_str(data)

        global measurements
        measurement = decode_data_pvvx(mac, adv_type, data_str, rssi)
        if measurement:
            print(measurement)
            measurements.append(measurement)


    if WATCHDOG_TIMER:
        keepingLEScanRunningThread = threading.Thread(target=keepingLEScanRunning)
        keepingLEScanRunningThread.start()

    # Blocking call (the given handler will be called each time a new LE
    # advertisement packet is detected)
    parse_le_advertising_events(sock,
                                handler=le_advertise_packet_handler,
                                debug=False)
except KeyboardInterrupt:
    disable_le_scan(sock)
