#!/usr/bin/env python

import json
import urllib.request
import zoneinfo
from datetime import datetime, timedelta, timezone

import humanize

import telegram

KPI_THRESHOLD = 6
CLOUD_THRESHOLD = 50
userAgent = "playground sergey@melnikov.no"
city = "Oslo"
latitude = 59.948
longitude = 10.767

# city = "Kirkenes"
# latitude = 69.73
# longitude = 30.05
now = datetime.utcnow().replace(tzinfo=timezone.utc)
metno_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
kpi_url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"


sun_today_url = f"https://api.met.no/weatherapi/sunrise/3.0/sun?lat={latitude}&lon={longitude}&date={now.date()}"
sun_tomorrow_url = f"https://api.met.no/weatherapi/sunrise/3.0/sun?lat={latitude}&lon={longitude}&date={(now + timedelta(days=1)).date()}"
sunset_str = json.loads(urllib.request.urlopen(
    urllib.request.Request(sun_today_url, headers={'User-Agent': userAgent})).read()
                        )["properties"]["sunset"]["time"]
sunrise_str = json.loads(urllib.request.urlopen(
    urllib.request.Request(sun_tomorrow_url, headers={'User-Agent': userAgent})).read()
                         )["properties"]["sunrise"]["time"]
try:
    sunset = datetime.fromisoformat(sunset_str)
    sunrise = datetime.fromisoformat(sunrise_str)
except:
    sunset = sunrise = None
    # sunset = datetime.fromisoformat("2023-11-26T11:19:00+01:00")
    # sunrise = datetime.fromisoformat("2024-01-16T10:44:00+01:00")

def timeDescription(time):
    if sunset:
        return (f"{humanize.naturaldelta(time - sunset)} after sunset, "
                f"{humanize.naturaldelta(sunrise - time)} before sunrise. ")
    else:
        return "Polar night. "

def isNighttime(time):
    if sunset:
        return sunset < time < sunrise
    else:
        return True


met_data = json.loads(urllib.request.urlopen(
    urllib.request.Request(metno_url, headers={'User-Agent': userAgent})).read()
                      )["properties"]["timeseries"]


def getClouds(time: datetime):
    for record in met_data:
        r_time = datetime.strptime(
            record["time"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)

        if time == r_time:
            return float(record["data"]["instant"]["details"]["cloud_area_fraction"])
    return float("nan")


kpi_data = json.loads(urllib.request.urlopen(kpi_url).read())[1:]
tz_oslo = zoneinfo.ZoneInfo("Europe/Oslo")

messages = []
for row in kpi_data:
    time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    if time < now - timedelta(hours=0) or time > now + timedelta(hours=24):
        continue
    if not isNighttime(time):
        continue
    kpi = float(row[1])
    cloudsPercent = getClouds(time)
    # print(time, kpi, cloudsPercent)
    if kpi >= KPI_THRESHOLD and cloudsPercent < CLOUD_THRESHOLD:
        message = (
                f"Kp {kpi} is expected in {humanize.naturaltime(now - time)}, " +
                timeDescription(time) +
                f"Clouds will be at {cloudsPercent}%. "
        )
        messages.append(message)

if messages:
    messages.append(f"at {city}")
    print(messages)
    telegram.sendMessage("\n".join(messages))
