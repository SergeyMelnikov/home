#!/usr/bin/env python

import json
import urllib.request
import zoneinfo
from datetime import datetime, timedelta, timezone

import humanize

import telegram

userAgent = "playground sergey@melnikov.no"
# Oslo
latitude = 59.948
longitude = 10.767
# Kirkenes
# latitude = 69.73
# longitude = 30.05
now = datetime.utcnow().replace(tzinfo=timezone.utc)
metno_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
# metno_url = "https://melnikov.no/metno.json"
kpi_url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
# kpi_url = "https://melnikov.no/noaa-planetary-k-index-forecast.json"

sun_today_url = f"https://api.met.no/weatherapi/sunrise/3.0/sun?lat={latitude}&lon={longitude}&date={now.date()}"
sun_tomorrow_url = f"https://api.met.no/weatherapi/sunrise/3.0/sun?lat={latitude}&lon={longitude}&date={(now + timedelta(days=1)).date()}"
try:
    sunset = datetime.fromisoformat(json.loads(urllib.request.urlopen(
        urllib.request.Request(sun_today_url, headers={'User-Agent': userAgent})).read()
                                               )["properties"]["sunset"]["time"])
except:
    sunset = datetime.fromisoformat("2023-11-26T10:19:00Z")
try:
    sunrise = datetime.fromisoformat(json.loads(urllib.request.urlopen(
        urllib.request.Request(sun_tomorrow_url, headers={'User-Agent': userAgent})).read()
                                                )["properties"]["sunrise"]["time"])
except:
    sunrise = datetime.fromisoformat("2024-01-16T09:44:00Z")

met_data = json.loads(urllib.request.urlopen(
    urllib.request.Request(metno_url, headers={'User-Agent': userAgent})).read()
                      )["properties"]["timeseries"]


def getClouds(time: datetime):
    for record in met_data:
        r_time = datetime.fromisoformat(record["time"])
        if time == r_time:
            return float(record["data"]["instant"]["details"]["cloud_area_fraction"])
    return float("nan")


data = json.loads(urllib.request.urlopen(kpi_url).read())[1:]
tz_oslo = zoneinfo.ZoneInfo("Europe/Oslo")

messages = []
for row in data:
    time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    if time < now - timedelta(hours=0) or time > now + timedelta(hours=12):
        continue
    if time < sunset or time > sunrise:
        continue
    kpi = float(row[1])
    cloudsPercent = getClouds(time)
    if kpi >= 6 and cloudsPercent < 50:
        message = (
            f"Kp {kpi} is expected in {humanize.naturaltime(now - time)}, "
            f"{humanize.naturaldelta(time - sunset)} after sunset, "
            f"{humanize.naturaldelta(sunrise - time)} before sunrise. "
            f"Clouds will be at {cloudsPercent}%. "
        )
        messages.append(message)

if messages:
    print(messages)
    telegram.sendMessage("\n".join(messages))
