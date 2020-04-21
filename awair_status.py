#!/usr/bin/python3
import json
import sys

import pymorphy2

morph = pymorphy2.MorphAnalyzer()


def make_word(x, word):
    parse = morph.parse(word)[0]
    return parse.make_agree_with_number(x).word


data = json.load(sys.stdin)

temperature = int(data["temp"])
degrees = make_word(temperature, 'градус')
co2 = int(data["co2"])
humidity = int(data["humid"])
percent = make_word(humidity, 'процент')

print(f'Температура {temperature} {degrees}. Цэ О Два {co2}. Влажность {humidity} {percent}.')
