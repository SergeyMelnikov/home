#!/usr/bin/python3

import json
import urllib

from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.Client import Client
from huawei_lte_api.enums.sms import BoxTypeEnum

chat_id = '-386960468'
token = '1051873449:AAHG4I6vScNW061TlPQ8I7zNOLvPncADCz4'


connection = AuthorizedConnection('http://192.168.2.1', 'admin', 'admin')
client = Client(connection)

while True:
    sms = client.sms.get_sms_list(1, BoxTypeEnum.LOCAL_INBOX, 1, 0, 0, 1)
    if sms['Messages'] is None:
        exit(0)
    print(sms)
    sender = sms['Messages']['Message']['Phone']
    date = sms['Messages']['Message']['Date']
    text = sms['Messages']['Message']['Content']
    sms_index = sms['Messages']['Message']['Index']
    unread = sms['Messages']['Message']['Smstat'] == '0'
    notification = f'SMS from {sender}\nDate: {date}\n{text}'
    print(notification)
    print(f'is_unread = {unread}')
    if not unread:
        break

    url = f'https://api.telegram.org/bot{token}/sendMessage'

    data = {'chat_id': chat_id, 'text': notification}
    data = urllib.parse.urlencode(data).encode()

    req = urllib.request.Request(url, data=data)
    response = json.loads(urllib.request.urlopen(req).read())
    print(response)
    if response['ok']:
        client.sms.set_read(sms_index)
    else:
        break
