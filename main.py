import os
import re
import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import InvalidArgumentException


options = webdriver.ChromeOptions()
options.binary_location = os.environ.get('GOOGLE_CHROME_SHIM', None)
options.add_argument('--disable-gpu')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("headless")
options.add_argument('window-size=0x0')

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton('songsterr')
    markup.add(button)
    bot.send_message(message.chat.id, 'Для работы данному боту необходима ссылка на табулатуру с сайта www.songsterr.com', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_songsterr(message):
    if message.text == 'songsterr':
        bot.send_message(message.chat.id, 'https://www.songsterr.com/')
    else:
        get_tab(message)


@bot.message_handler(content_types=['text'])
def get_tab(message):
    try:
        url = message.text
        driver = webdriver.Chrome(executable_path="chromedriver", options=options)
        driver.get(url=url)
        source_page = driver.page_source
        soup = BeautifulSoup(source_page, 'lxml')
        fut_js = soup.find('script', type="application/json").text
        artist_raw = re.findall("""("artist":"[\.?A-Za-zА-Яа-я!()&\\\\u002F\\\'\- \-&]+")""", fut_js)
        artist = re.sub(r'\?|:|!|u002F|\\|\/|\.|\(|\)', '', artist_raw[0])
        song_raw = re.findall("""("title":"[\.?A-Za-zА-Яа-я!\(\)&\\\\u002F\\\'\- \-&]+")""", fut_js)
        song = re.sub(r'\?|:|!|u002F|\\|\/|\.', '', song_raw[0])
        revision_id = re.findall('"revisionId":\w\d+', fut_js)
        for i in revision_id:
            a = re.findall('\d+', i)
        scam_url = f'https://www.songsterr.com/a/ra/player/songrevision/{int(a[0])}.xml'
        driver.get(url=scam_url)
        source_page = driver.page_source
        soup = BeautifulSoup(source_page, 'lxml')
        gp5 = soup.find('div', {'id': 'webkit-xml-viewer-source-xml'}).text
        gp_raw_link = re.findall('.+gp5|.+gp4|.+gp3', gp5)
        gp_url = str(gp_raw_link)
        gp_link = re.findall('[A-Za-z:\/ 0-9.\-]+', gp_url)
        r = requests.get(gp_link[0])
        filename_raw = str(artist)[9:-1] + ' - ' + str(song)[8:-1] + '.gp5'
        filename = filename_raw.replace('\\', '')
        if '&' in filename:
            filename = filename.replace('&', 'and')
        open(filename, 'wb').write(r.content)
        bot.send_document(message.chat.id, open(filename, 'rb'))
        os.remove(filename)

    except (AttributeError, InvalidArgumentException):
        bot.send_message(message.chat.id, 'Введите корректную ссылку на табулатуру')


bot.polling()

