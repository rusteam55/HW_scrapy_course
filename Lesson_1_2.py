# Lesson_1_parsing_api
# 2. Изучить список открытых API. Найти среди них любое, требующее авторизацию (любого типа).
# Выполнить запросы к нему, пройдя авторизацию. Ответ сервера записать в файл.
# Ресурс для выбора api: https://www.programmableweb.com/apis/directory

# Выберем ресурс с финансовыми данными: стоимость акций, валют, фондов и т.п.: https://twelvedata.com
# https://api.twelvedata.com/time_series?symbol=PFE&interval=15min&apikey=????

import requests
import json
from pprint import pprint

base_url = 'https://api.twelvedata.com/time_series' # просмотр котировок по акциям
api_key = '668f80cc9579438689ef54b5542cb28c'
stocks = 'PFE' # искомый инструмент (акции фармацевтической компании Pfizer)
interval = '15min' # интервал анализируемых свечей (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 8h, 1day, 1week, 1month')
params = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4434.0 Safari/537.36',
           'symbol': stocks,
           'interval': interval,
           'apikey': api_key
           }

response = requests.get(base_url, params=params)
# pprint(response.text)

# сформируем json-вывод:
if response.ok:
    data = response.json()
# pprint(data)

# сохраним json-вывод в файле:
if response.ok:
    path = "stocks_price_list.json"
    with open(path,'w') as f:
        json.dump(data, f)
