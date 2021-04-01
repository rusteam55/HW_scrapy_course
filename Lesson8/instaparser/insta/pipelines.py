# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from itemadapter import ItemAdapter
from insta.items import InstaItem
from scrapy import Spider
from pymongo import MongoClient

class InstaPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongoDB = client.instagram
        self.collection = self.mongoDB['user_rel']

    def process_item(self, item: InstaItem, spider: Spider):
        self.collection.insert(item)
        return item
