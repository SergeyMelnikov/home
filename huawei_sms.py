from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.Client import Client
from huawei_lte_api.enums.sms import BoxTypeEnum

connection = AuthorizedConnection("http://192.168.2.1", "admin", "admin")
client = Client(connection)
print(client.sms.get_sms_list())
sms = client.sms.get_sms_list(1, BoxTypeEnum.LOCAL_INBOX, 1, 0, 0, 1)
if sms['Messages'] is None:
    exit(0)
print(sms)
print('SMS from ' + sms['Messages']['Message']['Phone'])
print("Date:" + sms['Messages']['Message']['Date'])
print("Content: " + sms['Messages']['Message']['Content'])
client.sms.set_read()
