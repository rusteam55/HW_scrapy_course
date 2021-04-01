# Lesson_8: Парсинг Instagram
# 1) Написать приложение, которое будет проходиться по указанному списку
# (делать через ввод input) двух и/или более пользователей и собирать данные
# об их подписчиках и подписках.

# 2) По каждому пользователю, который является подписчиком или на которого
# подписан исследуемый объект нужно извлечь имя, id, фото (остальные данные по желанию).
# Фото можно дополнительно скачать(необязательно).

# 3) Собранные данные необходимо сложить в базу данных.
# Структуру данных нужно заранее продумать(!), чтобы:

# 4) Написать функцию, которая будет делать запрос к базе, который вернет
# список подписчиков только указанного пользователя

# 5) Написать функцию, которая будет делать запрос к базе, который вернет
# список профилей, на кого подписан указанный пользователь



from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from insta import settings
from insta.spiders.insta_parser import InstaParserSpider
from pymongo import MongoClient

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(settings= crawler_settings)
    process.crawl(InstaParserSpider)

    process.start()
    print('xxxxxxxxxxxxxxxxxxxxxxxxxxxx')

    # task 3-5
    client = MongoClient('localhost', 27017)
    mongo_DB = client.instagram
    collection = mongo_DB['user_rel']

    # запрос к базе, который вернет список подписчиков только указанного пользователя
    task4 = collection.find({'parsed_username': 'pfc_cska', 'relation': 'subscriber'})
    for n in task4:
        print(n)

    # запрос к базе, который вернет список профилей, на кого подписан указанный пользователь
    task5 = collection.find({'parsed_username': 'dobriy_mir', 'relation': 'subscribe'})
    for n in task5:
        print(n)