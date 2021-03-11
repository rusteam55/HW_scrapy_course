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


# 1) Функция, создающая базу данных:
def mongodb_func():
    client = MongoClient('127.0.0.1', 27017)
    database = client['vacancyDB']
    return database


# запуск функции для сбора вакансий в БД.
db = mongodb_func()
# создадим две коллекции по источнику данных:
collection_hhru = db.hhru
collection_sjru = db.sjru


# 2) Перед перебором и записью данных создадим функцию,
# проверяющую вакансию на наличие в БД (если данные отсутствуют в коллекции, то добавляем)
def paste_new_vacancy_func(collection, vacancy_data):
    if not collection.find_one(vacancy_data):
        collection.insert_one(vacancy_data)


# 3) Сбор данных и добавление их в соответствующую коллекцию
text = input('Поиск вакансий в банковской сфере в Москве и области. Введите искомую вакансию... ')

# Поиск по HH.ru:
# Формируем параметры ссылки
main_link_hh = 'https://hh.ru'
params = {'area': '1',  # Москва
          'clusters': 'true',
          'enable_snippets': 'true',
          'text': text,
          'specialization': '5',  # Банки
          'from': 'cluster_professionalArea',
          'showClusters': 'true',
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
        vacancy_data = {}
        # поиск наименования вакансии:
        vacancy_title = vacancy.find('div', {'class': 'vacancy-serp-item__info'})
        vacancy_name = vacancy_title.getText()
        # поиск зп:
        vacancy_salary = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
        if not vacancy_salary:
            salary_min = None
            salary_max = None
            salary_currency = None
        else:
            vacancy_salary = vacancy_salary.getText()
            vacancy_salary = vacancy_salary.replace('\xa0', '')
            vacancy_salary = vacancy_salary.replace('-', ' ')
            vacancy_salary = vacancy_salary.split()

            if vacancy_salary[0] == 'до':
                salary_min = None
                salary_max = int(vacancy_salary[1])
                salary_currency = vacancy_salary[2]
            elif vacancy_salary[0] == 'от':
                salary_min = int(vacancy_salary[1])
                salary_max = None
                salary_currency = vacancy_salary[2]
            else:
                salary_min = int(vacancy_salary[0])
                salary_max = int(vacancy_salary[1])
                salary_currency = vacancy_salary[2]
        # поиск ссылки на вакансию:
        vacancy_link = vacancy_title.find('a')['href']

        # поиск работодателя:
        vacancy_company = vacancy.find('div', {'class': 'vacancy-serp-item__meta-info-company'})
        vacancy_employer = vacancy_company.getText()

        # заполняем словарь данных:
        vacancy_data['name'] = vacancy_name
        vacancy_data['salary_min'] = salary_min
        vacancy_data['salary_max'] = salary_max
        vacancy_data['currency'] = salary_currency
        vacancy_data['link'] = vacancy_link
        vacancy_data['employer'] = vacancy_employer
        vacancy_data['site'] = 'hh.ru'

        # запишем данные в коллекцию  MongoDB с помощью функции,
        # которая предварительно проверяет на наличие этих данных в коллекции:
        paste_new_vacancy_func(collection_hhru, vacancy_data)

# Поиск по superjob.ru
# https://www.superjob.ru/vacancy/search/?keywords=кредитование&catalogues%5B0%5D=381&geo=4&click_from=facet

main_link_sj = 'https://superjob.ru'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4440.0 Safari/537.36'}
params = {
    'keywords': text,
    'catalogues': {'382', '383', '384', '385', '386', '387', '388', '389', '390', '391', '392', '393', '394', '395',
                   '396', '397', '398', '399', '400', '401', '402', '403', '404', '405', '406', '407', '408', '411',
                   '412', '413'},  # банки
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
        vacancy_data = {}
        # поиск наименования вакансии:
        vacancy_title = vacancy.find('div', {'class': ['_3mfro PlM3e _2JVkc _3LJqf']})
        vacancy_name = vacancy_title.get_text() if vacancy_title else ''
        # поиск ссылки на вакансию:
        vacancy_link = main_link_sj + vacancy_title.next['href'] if vacancy_title else ''

        # поиск зп:
        vacancy_salary = vacancy.find('span', {'class': ['_3mfro _2Wp8I PlM3e _2JVkc _2VHxz']})
        salary_min = None
        salary_max = None
        salary_currency = None
        if vacancy_salary:
            vacancy_salary = vacancy_salary.text
            if vacancy_salary.find('от') != -1:
                salary_min = int(''.join([char for char in vacancy_salary if char.isdigit()]))
                salary_currency = vacancy_salary[-4:]
            if vacancy_salary.find('до') != -1:
                salary_max = (''.join([char for char in vacancy_salary if char.isdigit()]))
                salary_currency = vacancy_salary[-4:]
            if vacancy_salary.find('—') != -1:
                salary_min = int(''.join([char for char in vacancy_salary.split('—')[0] if char.isdigit()]))
                salary_max = int(''.join([char for char in vacancy_salary.split('—')[1] if char.isdigit()]))
                salary_currency = vacancy_salary[-4:]
            if vacancy_salary.find('договор') != -1:
                salary_min = None
                salary_max = None
                salary_currency = None

        # поиск работодателя:
        vacancy_company = vacancy.find('span', {'class': ['f-test-text-vacancy-item-company-name']})
        vacancy_employer = vacancy_company.getText()

        # заполняем словарь данных:
        vacancy_data['name'] = vacancy_name
        vacancy_data['salary_min'] = salary_min
        vacancy_data['salary_max'] = salary_max
        vacancy_data['currency'] = salary_currency
        vacancy_data['link'] = vacancy_link
        vacancy_data['employer'] = vacancy_employer
        vacancy_data['site'] = 'superjob.ru'

        # запишем данные в коллекцию  MongoDB с помощью функции,
        # которая предварительно проверяет на наличие этих данных в коллекции:
        paste_new_vacancy_func(collection_sjru, vacancy_data)

    # print()
    # если есть кнопка "дальше", то смена номера страницы и запуск цикла снова, иначе exit
    next_link = soup_sj.find('a', {'class': ['icMQ_ bs_sM _3ze9n f-test-button-dalshe f-test-link-Dalshe']})
    if next_link:
        params['page'] = str(int(params['page']) + 1)
    else:
        break


# 4. Функция, которая производит поиск и выводит на экран вакансии с заработной платой
# больше введённой суммы
def find_vacancies(collection, search_salary):
    return list(collection.find({'$or': [{'salary_min': {'$gte': search_salary}}, {'salary_max': {'$gte': search_salary}}]}))[:]


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
