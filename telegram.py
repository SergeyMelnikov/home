import json
import urllib, urllib.parse, urllib.request
from config import telegram_token, telegram_melnikov_id


def sendMessage(text):
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'

    data = {'chat_id': telegram_melnikov_id, 'text': text}
    data = urllib.parse.urlencode(data).encode()

    req = urllib.request.Request(url, data=data)
    response = json.loads(urllib.request.urlopen(req).read())
    print(response)
