# Lesson 7 Selenium
# Написать программу, которая собирает посты из группы https://vk.com/tokyofashion
#
# Будьте внимательны к сайту!
# Делайте задержки, не делайте частых запросов!
# 1) В программе должен быть ввод, который передается в поисковую строку по постам группы
# 2) Соберите данные постов:
# - Дата поста
# - Текст поста
# - Ссылка на пост(полная)
# - Ссылки на изображения(если они есть)
# - Количество лайков, "поделиться" и просмотров поста
# 3) Сохраните собранные данные в MongoDB
# 4) Скролльте страницу, чтобы получить больше постов(хотя бы 2-3 раза)
# 5) (Дополнительно, необязательно) Придумайте как можно скроллить "до конца" до тех пор пока посты не перестанут добавляться
# Чем пользоваться?
#
# Selenium, можно пользоваться lxml, BeautifulSoup

# Импортируем библиотеки:
import time
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urljoin
from pymongo import MongoClient

client = MongoClient('localhost', 27017)

# Хромдрайвер расположен в bin:
DRIVER_PATH = "chromedriver"

# Поисковый запрос к постам:
# keyword = input('Введите поисковый запрос к постам группы tokyofashion ...')
# print(keyword)

# Запускаем загрузку страницы:
url = "https://vk.com/tokyofashion"
driver = webdriver.Chrome(DRIVER_PATH)
driver.get(url)
driver.refresh()

# Открываем поисковую строку:
search_url = driver.find_element_by_class_name('ui_tab_search').get_attribute('href')

# Запускаем загрузку страницы с поисковым запросом:
driver.get(search_url)

# Передаем поисковый запрос:
search = driver.find_element_by_id("wall_search")
search.send_keys('одежда')
search.send_keys(Keys.ENTER)

scrollpage = 1
while True:
    time.sleep(2)
    try:
        button = driver.find_element_by_class_name('JoinForm__notNow')
        if button:
            button.click()
    except Exception as e:
        print(e)
    finally:
        driver.find_element_by_tag_name("html").send_keys(Keys.END)
        scrollpage += 1
        time.sleep(1)
        # поиск конца стены постов
        wall = driver.find_element_by_id('fw_load_more')
        stopscroll = wall.get_attribute('style')
        # print(stopscroll)
        if stopscroll == 'display: none;':
            break
# print(scrollpage)
posts = driver.find_elements_by_xpath('//div[@id="page_wall_posts"]//..//img[contains(@alt,"Tokyo Fashion")]/../../..')
# print(posts[0])

p=0
posts_info = []
for post in posts:
    post_data = {}
    post_day = post.find_element_by_class_name('rel_date').text
    post_text = post.find_element_by_class_name('wall_post_text').text
    post_link = post.find_element_by_class_name('post_link').get_attribute('href')
    post_photo_links_list = []
    post_photo_links = post.find_elements_by_xpath('.//a[contains(@aria-label,"Original")]')
    for photo in post_photo_links:
        photo_link = photo.get_attribute('aria-label').split()[2]
        post_photo_links_list.append(photo_link)
    post_likes = int(post.find_elements_by_class_name('like_button_count')[0].text)
    post_share = int(post.find_elements_by_class_name('like_button_count')[1].text)
    # post_views = int(post.find_elements_by_xpath('.//div[contains(@class,"like_views")]')[0].get_attribute('title').split()[0])

    # соберем словарь:
    post_data['post_day'] = post_day
    post_data['post_text'] = post_text
    post_data['post_link'] = post_link
    post_data['post_photo_links_list'] = post_photo_links_list
    post_data['post_likes'] = post_likes
    post_data['post_share'] = post_share
    # post_data['post_views'] = post_views

    # сформируем список:
    posts_info.append(post_data)
    p += 1
    print(p)

# pprint(posts_info)


db = client['tokyo_posts']
collection = db.collection
collection.insert_many(posts_info)