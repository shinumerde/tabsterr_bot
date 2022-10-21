import os
import re
import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import InvalidArgumentException

import data

options = webdriver.ChromeOptions()
options.binary_location = os.environ.get('GOOGLE_CHROME_SHIM', None)
options.add_argument('--disable-gpu')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("headless")
options.add_argument('window-size=0x0')

bot = telebot.TeleBot(data.TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton('www.songsterr.com', url='https://www.songsterr.com/')
    markup.add(button)
    bot.send_message(message.chat.id, 'Для работы данному боту необходима ссылка на табулатуру с сайта www.songsterr.com', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def send_welcome(message):
    try:
        url = message.text
        driver = webdriver.Chrome(executable_path="chromedriver", chrome_options=options)
        driver.get(url=url)
        source_page = driver.page_source
        soup = BeautifulSoup(source_page, 'lxml')
        fut_js = soup.find('script', type="application/json").text
        artist_raw = re.findall("""("artist":"[A-Za-z!&\\\\u002F\\\'\- \-&]+")""", fut_js)
        if 'u002F' in artist_raw[0]:
            artist = artist_raw[0].replace('u002F', '')
        else:
            artist = artist_raw[0]
        song = re.findall("""("title":"[A-Za-z!&\\\\u002F\\\'\- \-&]+")""", fut_js)
        revision_id = re.findall('"revisionId":\w\d+', fut_js)
        for i in revision_id:
            a = re.findall('\d+', i)
        scam_url = f'https://www.songsterr.com/a/ra/player/songrevision/{int(a[0])}.xml'
        driver.get(url=scam_url)
        source_page = driver.page_source
        soup = BeautifulSoup(source_page, 'lxml')
        gp5 = soup.find('div', {'id': 'webkit-xml-viewer-source-xml'}).text
        gp_raw_link = re.findall('.+gp5', gp5)
        gp_url = str(gp_raw_link)
        gp_link = re.findall('[A-Za-z:\/ 0-9.]+', gp_url)
        r = requests.get(gp_link[0])
        filename_raw = str(artist)[10:-1] + ' - ' + str(song)[11:-3] + '.gp5'
        filename = filename_raw.replace('\\', '')
        if '&' in filename:
            filename = filename.replace('&', 'and')
        open(filename, 'wb').write(r.content)
        bot.send_document(message.chat.id, open(filename, 'rb'))
        os.remove(filename)

    except (AttributeError, InvalidArgumentException):
        bot.send_message(message.chat.id, 'Введите корректную ссылку на табулатуру')


bot.polling()

