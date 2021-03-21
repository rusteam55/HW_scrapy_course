# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from jobparser.items import JobparserItem
from scrapy import Spider
# в вашем случае
MONGO_URL = "localhost:27017"



class JobparserPipeline:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client['vacancy']

    def process_item(self, item: JobparserItem, spider: Spider):
        collection = self.db[spider.name]
        item['min_salary'], item['max_salary'], item['currency'] = self.process_salary(item['salary'])
        collection.insert(item)
        # print()
        return item

    def clean_salary_list(self, salary_list: list):
        """
        Удаляем пробелы и пустые элементы списка
        Возвращает обработанный список
        """
        result_list = []
        for item in salary_list:
            item = item.strip().replace('\xa0', '').replace(' ', '')
            if item:
                result_list.append(item)
        return result_list

    def process_salary(self, salary: list):
        """
        Обработка полученных шаблонов зарплат
        """
        min_salary = None
        max_salary = None
        currency = None

        if salary:
            salary = self.clean_salary_list(salary)

            try:
                # поиск шаблона
                for i in range(0, len(salary)):
                    # если есть 'от' значит след элемент - это мин.зп.,
                    # за за следует элемент - валюта
                    if salary[i] == 'от':
                        min_salary = int(''.join([i for i in salary[i + 1] if i.isdigit()]))
                        currency = salary[i + 2]

                    # если есть '-' значит предыдущий элемент это мин. зп.,
                    # и значит следующий элемент - макс. зп
                    # а следом за макс.зп. - валюта
                    if salary[i] == '—':
                        min_salary = int(''.join([i for i in salary[i - 1] if i.isdigit()]))
                        max_salary = int(''.join([i for i in salary[i + 1] if i.isdigit()]))
                        currency = salary[i + 2]

                    # если есть 'до', значит следующий элемент - макс. зп,
                    # а следующий за ней элемент - это валюта
                    if salary[i] == 'до':
                        max_salary = int(''.join([i for i in salary[i + 1] if i.isdigit()]))
                        currency = salary[i + 2]

                    # шаблон из superjob:
                    # найдем '/', а перед ним возьмем все нечисловые символы
                    if salary[i] == '/':
                        currency = (''.join([i for i in salary[i - 1] if not i.isdigit()]))

            except IndexError:
                pass  # пропускаем если данные отсутствуют / зарплата не соответствует шаблону

        return min_salary, max_salary, currency