# Lesson_3_СУБД_MongoDB
# 1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию,
# записывающую собранные вакансии в созданную БД.
# 2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введённой суммы.
# 3. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта.

from bs4 import BeautifulSoup as bs
import requests
from pprint import pprint
import pandas as pd
from pymongo import MongoClient


# 1) Функция, инициализации базы данных:
def mongodb_func():
    client = MongoClient('127.0.0.1', 27017)
    database = client['vacancyDB']
    return database

# # 2) Перед перебором и записью данных создадим функцию,
# # проверяющую вакансию на наличие в БД (если данные отсутствуют в коллекции, то добавляем)
# def paste_new_vacancy_func(collection, vacancy_data):
#     if not collection.find_one(vacancy_data):
#         collection.insert_one(vacancy_data)

# 2) Функция обновления и добавления новых вакансий:
def insert_vac_if_not_exists(collection, filter, vacancy_data) -> object:
    collection.update_one(filter, {'$set': vacancy_data}, upsert=True)
    # описание работы функции:
    # - передаем в качестве filter уникальную ссылку на вакансию,
    # - если ссылка есть, то '$set' позволяет обновить данные (перезапись данных vacancy_data),
    # - если ссылки нет, то upsert=True позволяет записать новые данные, которые не совпали с filter

# 3). Функция, которая производит поиск и выводит на экран вакансии с заработной платой
# больше введённой суммы
def find_vacancies(collection, search_salary):
    return list(collection.find({'$or': [{'salary_min': {'$gte': search_salary}}, {'salary_max': {'$gte': search_salary}}]}))[:]


# Создаем/запускаем БД:
db = mongodb_func()


# Создадим две коллекции по источнику данных:
collection_hhru = db.hhru
collection_sjru = db.sjru


# Сбор данных и добавление их в соответствующую коллекцию
text = input('Поиск вакансий в Москве и области. Введите искомую вакансию... ')

"""
# Поиск по HH.ru:
"""

# Формируем параметры ссылки
main_link_hh = 'https://hh.ru'
params = {'area': '1',  # Москва
          'text': text,
          'page': ''}  # номер страницы будет передаваться в цикле при переборе всех страниц
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4440.0 Safari/537.36'}

# Запрашиваем страницу и создаем объект bs
response = requests.get(main_link_hh + '/search/vacancy', params=params, headers=headers)
soup = bs(response.text, 'html.parser')

# Найдем последнюю страницу
find_pager_block = soup.find('div', {'data-qa': 'pager-block'})
if not find_pager_block:
    last_page = 1
else:
    last_page = int(find_pager_block.find_all('a', {'class': 'HH-Pager-Control'})[
                        -2].getText())  # [-1] это кнопка дальше, [-2] это кнопка с номером последней страницы
# print(last_page)
# print()


# Перебираем страницы для сбора информации
for page in range(0, last_page):
    params['page'] = page
    response_hh = requests.get(main_link_hh + '/search/vacancy', params=params, headers=headers)
    soup_hh = bs(response_hh.text, 'html.parser')
    # выводим список вакансий на данной странице
    vacancy_list = soup_hh.findAll('div', {
        'data-qa': ['vacancy-serp__vacancy', 'vacancy-serp__vacancy vacancy-serp__vacancy_premium']})

    for vacancy in vacancy_list:
        vacancy_data = {'site': 'hh.ru'}
        # поиск наименования вакансии:
        vacancy_title = vacancy.find('div', {'class': 'vacancy-serp-item__info'})
        vacancy_data['name'] = vacancy_title.getText()
        # поиск зп:
        vacancy_salary = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
        if not vacancy_salary:
            vacancy_data['salary_min'] = None
            vacancy_data['salary_max'] = None
            vacancy_data['currency'] = None
        else:
            vacancy_salary = vacancy_salary.getText()
            vacancy_salary = vacancy_salary.replace('\xa0', '')
            vacancy_salary = vacancy_salary.replace('-', ' ')
            vacancy_salary = vacancy_salary.split()

            if vacancy_salary[0] == 'до':
                vacancy_data['salary_min'] = None
                vacancy_data['salary_max'] = int(vacancy_salary[1])
                vacancy_data['currency'] = vacancy_salary[2]
            elif vacancy_salary[0] == 'от':
                vacancy_data['salary_min'] = int(vacancy_salary[1])
                vacancy_data['salary_max'] = None
                vacancy_data['currency'] = vacancy_salary[2]
            else:
                vacancy_data['salary_min'] = int(vacancy_salary[0])
                vacancy_data['salary_max'] = int(vacancy_salary[1])
                vacancy_data['currency'] = vacancy_salary[2]
        # поиск ссылки на вакансию:
        vacancy_data['link'] = vacancy_title.find('a')['href']
        # поиск работодателя:
        vacancy_company = vacancy.find('div', {'class': 'vacancy-serp-item__meta-info-company'})
        vacancy_data['employer'] = vacancy_company.getText()

        # запишем данные в коллекцию  MongoDB с помощью функции,
        # которая предварительно проверяет на наличие этих данных в коллекции:
        insert_vac_if_not_exists(collection_hhru, {'link': vacancy_data.get('link')}, vacancy_data)
        #pprint(vacancy_data)


"""
Поиск по superjob.ru
https://www.superjob.ru/vacancy/search/?keywords=кредитование&geo=4&click_from=facet

"""

main_link_sj = 'https://superjob.ru'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4440.0 Safari/537.36'}
params = {
    'keywords': text,
    'geo': 4,  # Москва
    'click_from': 'facet',
    'page': '1'
}

# Будем перебирать страницы до тех пор пока будет отражаться кнопка "Дальше"
while True:
    response_sj = requests.get(main_link_sj + '/vacancy/search/', headers=headers, params=params)
    soup_sj = bs(response_sj.text, 'html.parser')
    vacancy_list = soup_sj.find_all('div', {'class': ['iJCa5 f-test-vacancy-item _1fma_ undefined _2nteL',
                                                      'iJCa5 f-test-vacancy-item _1fma_ undefined _2p0TS _2nteL']})

    # парсинг страницы
    for vacancy in vacancy_list:
        vacancy_data = {'site': 'superjob.ru'}
        # поиск наименования вакансии:
        vacancy_title = vacancy.find('div', {'class': ['_3mfro PlM3e _2JVkc _3LJqf']})
        if vacancy_title:
            vacancy_data['name'] = vacancy_title.get_text()
        else:
            vacancy_data['name'] = None
        # поиск ссылки на вакансию:
        if vacancy_title:
            vacancy_data['link'] = main_link_sj + vacancy_title.next['href']
        else:
            vacancy_data['link'] = None

        # поиск зп:
        vacancy_salary = vacancy.find('span', {'class': ['_3mfro _2Wp8I PlM3e _2JVkc _2VHxz']})
        vacancy_data['salary_min'] = None
        vacancy_data['salary_max'] = None
        vacancy_data['currency'] = None
        if vacancy_salary:
            vacancy_salary = vacancy_salary.text
            if vacancy_salary.find('от') != -1:
                vacancy_data['salary_min'] = int(''.join([char for char in vacancy_salary if char.isdigit()]))
                vacancy_data['currency'] = vacancy_salary[-4:]
            if vacancy_salary.find('до') != -1:
                vacancy_data['salary_max'] = (''.join([char for char in vacancy_salary if char.isdigit()]))
                vacancy_data['currency'] = vacancy_salary[-4:]
            if vacancy_salary.find('—') != -1:
                vacancy_data['salary_min'] = int(''.join([char for char in vacancy_salary.split('—')[0] if char.isdigit()]))
                vacancy_data['salary_max'] = int(''.join([char for char in vacancy_salary.split('—')[1] if char.isdigit()]))
                vacancy_data['currency'] = vacancy_salary[-4:]
            if vacancy_salary.find('договор') != -1:
                vacancy_data['salary_min'] = None
                vacancy_data['salary_max'] = None
                vacancy_data['currency'] = None

        # поиск работодателя:
        vacancy_company = vacancy.find('span', {'class': ['f-test-text-vacancy-item-company-name']})
        if vacancy_company is not None:
            vacancy_data['employer'] = vacancy_company.getText()
        else:
            vacancy_data['employer'] = None

        # print()
        # запишем данные в коллекцию  MongoDB с помощью функции,
        # которая предварительно проверяет на наличие этих данных в коллекции:
        insert_vac_if_not_exists(collection_sjru, {'link': vacancy_data.get('link')}, vacancy_data)

    # print()
    # если есть кнопка "дальше", то смена номера страницы и запуск цикла снова, иначе exit
    next_link = soup_sj.find('a', {'class': ['icMQ_ bs_sM _3ze9n f-test-button-dalshe f-test-link-Dalshe']})
    if next_link:
        params['page'] = str(int(params['page']) + 1)
    else:
        break


# поиск и вывод на экран вакансии с заработной платой больше введённой суммы:

search_salary = input('Введите минимальную зарплату для поиска вакансий на hhru: ... ')
if search_salary.isdigit():
    pprint(find_vacancies(collection_hhru, int(search_salary)))
else:
    pprint('Вы ввели нечисловое значение ')

search_salary = input('Введите минимальную зарплату для поиска вакансий на superjob.ru: ... ')
if search_salary.isdigit():
    pprint(find_vacancies(collection_sjru, int(search_salary)))
else:
    pprint('Вы ввели нечисловое значение')
