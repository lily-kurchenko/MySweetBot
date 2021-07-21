from bs4 import BeautifulSoup
import requests
import json
import telebot
from tqdm.notebook import tqdm
import six
import pandas as pd
import lxml

BOT_TOKEN = ''
WEATHER_TOKEN = ''

url = 'https://msk.kinoafisha.info/movies/'
html_text = requests.get(url).text
soup = BeautifulSoup(html_text, 'lxml')
n = 5

movies_html = soup.find('div', 'movieList movieList-grid grid')
movie_html_list = movies_html.find_all('div', 'movieList_item movieItem movieItem-grid grid_cell4')[:n]

movie_names = [movie_html.find('span', 'movieItem_title').text for movie_html in movie_html_list]
movie_genres = [movie_html.find('span', 'movieItem_genres').text for movie_html in movie_html_list]
movie_year = [movie_html.find('span', 'movieItem_year').text for movie_html in movie_html_list]
movie_mark = [movie_html.find('span', 'mark_num').text for movie_html in movie_html_list]

movie_url = [movie_html.find('a', href=True)['href'] for movie_html in movie_html_list]
s = 'visualEditorInsertion more_content'
movie_desk = [BeautifulSoup(requests.get(movie_url[i]).text, 'lxml').find('div', s).text for i in range(n)]

video_url = [f"{movie_url[i]}video/" for i in range(n)]
films = [[movie_names[i], movie_genres[i], movie_year[i], movie_mark[i], movie_desk[i].strip(), video_url[i]] for i in range(n)]
top_films = [f"{chr(10).join(films[i])}" for i in range(n)]

HREF_LEN = 35
urls = [f"https://msk.kinoafisha.info/movies/{movie_url[i][HREF_LEN:]}/#schedule" for i in range(n)]


def find_sessions(ind):
    sched_html = requests.get(urls[ind]).text
    soup_shed = BeautifulSoup(sched_html, 'lxml')
    m = 5

    cinema_html_list = soup_shed.find_all('div', 'showtimes_item')
    cinema_names = [(cinema_html.find('span', 'showtimesCinema_name')) for cinema_html in cinema_html_list]
    cinema_addr = [cinema_html.find('span', 'showtimesCinema_addr') for cinema_html in cinema_html_list]
    cinema_sessions = [cinema_html.find_all('a', 'showtimes_session session session-ticket ') for cinema_html in cinema_html_list]
    cnt = 0
    i = 0
    sessions = []
    cinemas = []
    while cnt < m and i < len(cinema_names):
        if cinema_names[i] is None or len(cinema_sessions[i]) == 0:
            i += 1
            continue
        info_cinema = [cinema_names[i].text, cinema_addr[i].text]
        cinemas.append(f"{chr(10).join(info_cinema)}")
        sessions_arr = [f"{session.find('span', 'session_time').text} {session.find('span', 'session_price').text}" for session in cinema_sessions[i]]
        sessions.append(f"{chr(10).join(sessions_arr)}")
        i += 1
        cnt += 1
    k = len(cinemas)
    cinemas_ans = [f"{chr(10).join([cinemas[i], sessions[i]])}" for i in range(k)]
    return cinemas_ans


def show_weather():
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q=Moscow&appid={WEATHER_TOKEN}"
    response = json.loads(requests.get(weather_url).text)
    return f"Будьте внимательны с погодой. \
    Температура на улице {round(response['main']['temp'] - 273.15, 1)} градусов Цельсия, ощущается как \
    {round(response['main']['feels_like'] - 273.15, 1)}."


bot = telebot.TeleBot(BOT_TOKEN)
my_commands = {'/start' '/top', '/help', '/1', '/first'}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Напишите /top, если хотите получить \
   описание топ-5 популярных фильмов,\
   которые можно посмотреть в московских кинотеатрах.\
   Изучите фильмы и выберите наиболее интересный. \
   Отправьте боту команду вида *число*, например, 2, чтобы \
   получить информацию о ближайших сеансах в 5 наиболее популярных \
   у вас кинотеатрах. Напишите /help, если вам нужна помощь.')


@bot.message_handler(commands=['top'])
def show_films(message):
    for i in range(n):
        bot.send_message(message.chat.id, top_films[i])
    bot.send_message(message.chat.id, 'Изучите фильмы и выберите наиболее интересный. \
  Отправьте боту команду вида *число*, например, 2, чтобы \
  получить информацию о ближайших сеансах в 5 наиболее популярных у вас кинотеатрах')


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "Напишите /top, если хотите получить \
  описание топ-5 популярных фильмов, \
  которые можно посмотреть в московских кинотеатрах. \
  Напишите номер понравившегося фильма в формате *3* (без звездочек), \
  если хотите узнать, когда, в каких кинотеатрах и \
  по какой цене его можно посмотреть")
    bot.send_message(message.chat.id, "Вот вам картинка с котиком, чтобы не было грустно :3")
    response = json.loads(requests.get("https://api.thecatapi.com/v1/images/search").text)
    bot.send_message(message.chat.id, response[0]['url'])


@bot.message_handler(
    func=lambda message: str(message.text).isdigit() and 1 <= int(message.text) <= 5)
def cinema_message(message):
    my_sessions = find_sessions(int(message.text) - 1)
    for i in range(len(my_sessions)):
        bot.send_message(message.chat.id, my_sessions[i])
    bot.send_message(message.chat.id, show_weather())


@bot.message_handler(func=lambda message: message not in my_commands)
def other_message(message):
    bot.send_message(message.chat.id, "Привет! Напишите /help, \
    если вам нужна помощь с командами. А пока ловите интересную цитату на английском :)")
    response = json.loads(requests.get("https://favqs.com/api/qotd").text)
    bot.send_message(message.chat.id, response["quote"]["body"])

print("ok")
bot.polling()
