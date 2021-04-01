import scrapy
from scrapy.http import HtmlResponse
from insta.items import InstaItem
import re
import json
from urllib.parse import urlencode
from copy import deepcopy

class InstaParserSpider(scrapy.Spider):
    name = 'insta_parser'
    allowed_domains = ['instagram.com']
    start_urls = ['https://instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    graphql_url = 'https://www.instagram.com/graphql/query/?'

    insta_login = 'spiderden4ik'
    insta_pwd = '#PWD_INSTAGRAM_BROWSER:9:1617312214:AVdQAIYiRn2CejLlImTdBRzu+NO9NZHOtmF9eGFurqReQMMzwOHQ41gl1jDRVCQxe9wqVDiuMZvFFz72ygIfw4mczdfqZ25eSNkjcEH/9QhwxwK1cxF7mld3B+RH8LgCwrVhUcnHkgkwSGe02LqLHIj3fSlK'

    # Список пользователей для парсинга
    parsed_users = ['pfc_cska', 'dobriy_mir']

    # переменная для переключения бора занных между подписками и подписчиками
    user_relations = {'subscriber': {'hash': 'c76146de99bb02f6415203be841dd25a',
                                     'json_group_name': 'edge_followed_by'
                                     },
                      'subscribe': {'hash': 'd04b0a864b4b54837c0d870b0e77e076',
                                    'json_group_name': 'edge_follow'
                                    }
                      }


    def parse(self, response: HtmlResponse):
        # извлекаем csrf token  из html
        csrf_token = self.fetch_csrf_token(response.text) # используем готовую функцию (на основе регулярных выражений)
        # заполняем форму, авторизируемся, ответ направляем в метод user_parse
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.user_parse,
            formdata={'username': self.insta_login, 'enc_password': self.insta_pwd},
            headers={'X-CSRFToken': csrf_token}
        )

    def user_parse(self, response: HtmlResponse):
        j_body = json.loads(response.text)
        # Проверяем ответ после авторизации
        if j_body['authenticated']:
            # Если авторизация ок, переходим на страницы пользователей.
            for parsed_user in self.parsed_users:
                # Для каждого пользователя вызываем запрос,
                # и ответ обрабатываем в методе user_data_parse
                yield response.follow(f'/{parsed_user}',
                                      callback=self.user_data_parse,
                                      cb_kwargs={'parsed_username': parsed_user})

    def user_data_parse(self, response: HtmlResponse, parsed_username):
        # Из ответа извлекаем id пользователя
        parsed_user_id = self.fetch_user_id(response.text, parsed_username)
        # Формируем словарь для передачи даных в запрос
        variables = {'id': parsed_user_id,
                     'include_reel': 'true',
                     'fetch_mutual': 'false',
                     "first": 50
                     }
        # Формируем ссылки для получения разных групп данных - подписчиках и подписках
        # Для каждой группы отношений запускаем запрос и ответ обрабатываем в user_relations_parse
        for group in self.user_relations.keys():
            url_posts = f'{self.graphql_url}query_hash={self.user_relations[group]["hash"]}&{urlencode(variables)}'
            yield response.follow(
                url_posts,
                callback=self.user_relations_parse,
                cb_kwargs={'parsed_username': parsed_username,
                           'parsed_user_id': parsed_user_id,
                           'relation': group,  # дополнительно передаем тип отношений
                           'variables': deepcopy(variables)}
            )

    def user_relations_parse(self, response: HtmlResponse, parsed_username, parsed_user_id, relation, variables):
        # Принимаем ответ.
        j_data = json.loads(response.text)
        page_info = j_data['data']['user'][self.user_relations[relation]['json_group_name']]['page_info']
        # Если есть следующая страница сохраняем курсор для перехода на следующую
        # и запускаем обработку этим же методом
        if page_info.get('has_next_page'):
            variables['after'] = page_info['end_cursor']
            url_posts = f'{self.graphql_url}query_hash={self.user_relations[relation]["hash"]}&{urlencode(variables)}'
            yield response.follow(
                url_posts,
                callback=self.user_relations_parse,
                cb_kwargs={'parsed_username': parsed_username,
                           'parsed_user_id': parsed_user_id,
                           'relation': relation,  # дополнительно передаем тип отношений
                           'variables': deepcopy(variables)}
            )

        # Обрабатывваем список, полученный в ответе и формируем элемент для скрапи
        users_list = j_data['data']['user'][self.user_relations[relation]['json_group_name']]['edges']
        # Перебираем пользователей из ответа, собираем данные
        for user in users_list:
            item = InstaItem(
                parsed_username=parsed_username,
                parsed_user_id=parsed_user_id,
                relation=relation,
                relation_user_id=user['node']['id'],
                relation_username=user['node']['username'],
                relation_user_pic=user['node']['profile_pic_url'],
                relation_user_all_data=user['node'],
            )
            yield item


    def fetch_csrf_token(self, text):
        """
        Получаем токен для авторизации
        """
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        """
        # Получаем id искомого пользователя
        """
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')