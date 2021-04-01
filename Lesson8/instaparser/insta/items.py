# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    _id = scrapy.Field()
    parsed_username = scrapy.Field()
    parsed_user_id = scrapy.Field()
    relation = scrapy.Field()
    relation_user_id = scrapy.Field()
    relation_username = scrapy.Field()
    relation_user_pic = scrapy.Field()
    relation_user_all_data = scrapy.Field()
    # pass
