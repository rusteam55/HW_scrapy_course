# Lesson4. lxml
# Используйте lxml, requests, pymongo
# 1. Написать приложение, которое собирает основные новости с сайтов:
# news.mail.ru, lenta.ru, yandex-новости.
# Для парсинга использовать XPath.
# Структура данных должна содержать:
# - название источника;
# - наименование новости;
# - ссылку на новость;
# - дата публикации.
# 2. Сложить собранные данные в БД(MongoDB).


from lxml import html
import requests
import time
from datetime import date, datetime, timedelta
from pymongo import MongoClient
from pprint import pprint
client = MongoClient('localhost', 27017)

# 1) Функция, инициализации базы данных:
def mongodb_func():
    client = MongoClient('127.0.0.1', 27017)
    database = client['topnewsDB']
    return database

# 2) Функция, проверяющая наличие новости в БД:
"""
Передаем в функцию коллекцию и данные по каждой новости
Если данные отсутствуют в коллекции, то происходит запись
"""
def paste_news_func(collection, news_data):
    if not collection.find_one(news_data):
        collection.insert_one(news_data)

# 3) Функция для получения DOM:
def dom_func(link):
    response = requests.get(link, headers=header)
    return html.fromstring(response.text)

header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4445.0 Safari/537.36'}

# 4) Функция для получения времени и источника новости на Mail.ru:
def get_data_mailru_func(link):
    dom = dom_func(link)
    time_ = datetime.strptime(dom.xpath("//div[contains(@class,'breadcrumbs')]//" +
                                          "span[contains(@class,'js-ago')]/@datetime")[0],
                               '%Y-%m-%dT%H:%M:%S%z')
    source_ = dom.xpath("//div[contains(@class,'breadcrumbs')]//span[@class='link__text']/text()")[0]
    return time_, source_

# 5) Функция для получения времени новости на Lenta.ru
def get_data_lentaru_func(link):
    dom = dom_func(link)
    time_ = datetime.strptime(dom.xpath("//div[@class='b-topic__info']/time/@datetime")[0], '%Y-%m-%dT%H:%M:%S%z')
    return time_



# Создаем/запускаем БД:
db = mongodb_func()


# Создадим три коллекции по источнику данных:
collection_lentaru = db.lentaru
collection_mailru = db.mailru
collection_yaru = db.yandexru


# Lenta.ru
main_link_lenta_news = 'https://lenta.ru'
dom = dom_func(main_link_lenta_news)

lenta_news = dom.xpath("//time[@class='g-time']/../..")

for news in lenta_news:
    lenta_news_data = {}
    title = news.xpath(".//time[@class='g-time']/../text()")
    link = main_link_lenta_news + news.xpath(".//time[@class='g-time']/../@href")[0]
    source = "lenta.ru"
    #запустим функцию, переходящую по ссылке и извлекающую дату/время
    time = get_data_lentaru_func(link)

    #Сформируем словарь:
    lenta_news_data['a_title'] = title[0].replace('\xa0', ' ')
    lenta_news_data['b_link'] = link
    lenta_news_data['c_source'] = source
    lenta_news_data['d_time'] = time

    # Сохраним данные в коллекции:
    paste_news_func(collection_lentaru, lenta_news_data)

    # pprint(lenta_news_data)


# Mail.ru
main_link_mail_news = 'https://news.mail.ru/'
dom = dom_func(main_link_mail_news)

mail_news = dom.xpath("//span[@class='photo__captions']/..|// li[@class='list__item']/a")

for news in mail_news:
    mail_news_data = {}
    title = news.xpath(".//text()")[0].replace('\xa0', ' ')
    link = news.xpath(".//@href")[0]

    # запустим функцию, переходящую по ссылке и извлекающую дату/время и источник
    time, source = get_data_mailru_func(link)

    # Сформируем словарь:
    mail_news_data['a_title'] = title
    mail_news_data['b_link'] = link
    mail_news_data['c_source'] = source
    mail_news_data['d_time'] = time

    # Сохраним данные в коллекции:
    paste_news_func(collection_mailru, mail_news_data)

    # pprint(mail_news_data)

# Yandex.ru
main_link_yandex_news = 'https://yandex.ru/news/'
dom = dom_func(main_link_yandex_news)

yandex_news = dom.xpath("//a[contains(@href,'rubric=index') and @class='mg-card__link']/ ancestor::article")

for news in yandex_news:
    yandex_news_data = {}
    title = news.xpath(".//h2/text()")[0].replace('\xa0', ' ')
    link = news.xpath(".//a/@href")[0]
    source = news.xpath(".//span[@class='mg-card-source__source']//text()")[0]
    time = news.xpath(".//span[@class='mg-card-source__time']//text()")[0]

    # Сформируем словарь:
    yandex_news_data['a_title'] = title
    yandex_news_data['b_link'] = link
    yandex_news_data['c_source'] = source
    yandex_news_data['d_time'] = str(datetime.combine(datetime.today().date(), datetime.strptime(time,"%H:%M").time()))

    # Сохраним данные в коллекции:
    paste_news_func(collection_yaru, yandex_news_data)

    # pprint(yandex_news_data)