# Lesson_1_parsing_api
# 1. Посмотреть документацию к API GitHub, разобраться как вывести список репозиториев для конкретного пользователя,
# сохранить JSON-вывод в файле *.json.

# Документация тут: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos
# Получение списка репозиториев: https://docs.github.com/en/rest/reference/repos#list-repositories-for-a-user
# Согласно документации запрос делается так: GET /users/{username}/repos

import requests
import json
from pprint import pprint

base_url = 'https://api.github.com'
username = 'rusteam55'

# найдем пользователя на github:
req = requests.get(f'{base_url}/users/{username}/repos')
# pprint(req.text)

# сформируем json-вывод:
if req.ok:
    data = req.json()
# pprint(data)

# сохраним json-вывод в файле:
if req.ok:
    path = "repositories_list.json"
    with open(path,'w') as f:
        json.dump(data, f)

# выведем список репозиториев:
for n in data:
    print(n['name'])