#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from telegram import Update
import logging
import sys
import pandas as pd
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import Filters, ConversationHandler, RegexHandler
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
import datetime
import requests
from forecaster import *

API_KEY_STOCKS = '7d15a0d24a2f5bd2efd71c393a73cfff'
API_KEY_NEWS = 'd033c9b32e714768818a5da1e8c285c4'
TOKEN = '1792902566:AAG_loiMwPNJutr_tYWXbCtRGfuOofFtLZA'
IMAGES_PATH = 'Media/'
CSV_PATH = 'Data/'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start_handler(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="""
    Привет! Я помогу тебе контролировать тебе твои стоки и принимать решение о покупке/продаже акций.
    Я могу:
    - предсказывать цену акции;
    - оценить дневную доходность акций;
    - прислать тебе новости о твоей компании.

    Предлагаю выбрать новую компанию за которой ты хочешь наблюдать. 
    Если ты знаешь тикер компании, добавь его в любимые компании с помощью команды /add_new_ticker <Имя тикера>.
    Если ты не знаешь тикер, то воспользуйся поиском с помощью команды /find_ticker <Имя тикера>.

    /find_ticker  <Имя компании> - Ищет по имени компании биржевой тикер.
    /add_new_ticker <Тикер> Добавление тикера в список избранных.
    /show_favorite_tickers - Показывает список любимых тикеров
    /delete_ticker <Тикер> Удаляет тикер из списка избранных.
    /get_news <Имя компании> <Количество дней> - Показывает новости по компании за последние 10 дней (если не указано количество дней)
    /get_prediction <Имя компании> <Количество дней>. Вместо Для просмотра прогноза по избранных компаниям используйте слово favorite вместо имени компаний. 

    """)


def find_companies(search_query: str) -> list:
    query = f"https://financialmodelingprep.com/api/v3/search?query={search_query}&limit=10&apikey={API_KEY_STOCKS}"
    result = requests.get(query)
    return result.json()

    
def find_ticker(update: Update, context: CallbackContext):
    company_name = context.args[0]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ищу компанию {company_name}. Минуточку...")
    try:
        companies_list = find_companies(company_name)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"По запросу {company_name} нашлось {len(companies_list)} котировок.")
        for company in companies_list:
            text = """Имя компании : {} \n 
                      Тикер компании : {} \n
                      Торгуется на бирже {} \n
                      Валюта : {}
                      """.format(company['name'],
                                 company['symbol'],
                                 company['stockExchange'],
                                 company['currency'])
            context.bot.send_message(chat_id=update.effective_chat.id, text=text
                                     )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Выбери нужный тикер и добавь его в любимые с помощью команды add_new_ticker <Имя тикера>.")
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"По запросу {company_name} ничего не найдено"
                                 )


def add_new_ticker(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    db_tickers = pd.read_csv(CSV_PATH + 'favorite_tickers.csv', index_col=0)
    if len(context.args) > 0:
        today = datetime.datetime.today().strftime('%m/%d/%Y')
        lastweek = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime('%m/%d/%Y')
        ticker = context.args[0]
        logging.info(f'ticker-{ticker}')
        try:
            data = get_data(ticker, start_date=lastweek, end_date=today, index_as_date=True, interval="1d")
            logging.info(f'Размер бд - {db_tickers.shape}')
            db_tickers = db_tickers.append({'chat_id': chat_id, 'ticker': ticker}, ignore_index=True)
            db_tickers.to_csv(CSV_PATH + 'favorite_tickers.csv')
            logging.info(f'Размер бд - {db_tickers.shape}')
            context.bot.send_message(chat_id=chat_id,
                                     text=f"Тикер {ticker} успешно добавлен в список ваших любимых тикеров.")
        except:
            context.bot.send_message(chat_id=chat_id,
                                     text=f"Пожалуйста, введите корректное название тикера. Например AMZN.😊")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text=f"Пожалуйста, введите название тикера после команды /add_new_ticker")

def create_table():
    try:
        db_tickers = pd.read_csv(CSV_PATH + 'favorite_tickers.csv', index_col=0)
        logger.info(f'Table favorite_tickers found. Shape - {db_tickers.shape}')
    except:
        logger.info(f'Creating new favorite_tickers table')
        db_tickers = pd.DataFrame()
        db_tickers = pd.DataFrame({'chat_id': [], 'ticker': []})
        db_tickers.to_csv(CSV_PATH + 'favorite_tickers.csv')


def show_favorite_tickers(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    db_tickers = pd.read_csv(CSV_PATH + 'favorite_tickers.csv', index_col=0)
    list_favorite = list(db_tickers[db_tickers['chat_id'] == chat_id]['ticker'].unique())
    if len(list_favorite) == 0:
        context.bot.send_message(chat_id=chat_id, text="У Вас еще нет любимых тикеров 🙁.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Список ваших любимых тикеров: ")
    for favorite in list_favorite:
        context.bot.send_message(chat_id=chat_id, text=favorite)


def delete_ticker(update: Update, context: CallbackContext):
    db_tickers = pd.read_csv(CSV_PATH + 'favorite_tickers.csv', index_col=0)
    chat_id = update.effective_chat.id
    if len(context.args) > 0:
        ticker = context.args[0]
        try:
            db_tickers.drop(db_tickers[(db_tickers['chat_id'] == chat_id) & (db_tickers['ticker'] == ticker)].index,
                            inplace=True)
            db_tickers.to_csv(CSV_PATH + 'favorite_tickers.csv')
            context.bot.send_message(chat_id=chat_id, text=f"Тикер {ticker} успешно удалён из избранных.")
        except:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Тикер {ticker} отсутсвовал в вашем избранном.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Пожалуйста, введите название тикера после команды /delete_ticker")


def get_news_articles(search_string, delay=10) -> list:
    since_date = (datetime.datetime.today() - datetime.timedelta(days=delay)).strftime('%Y-%m-%d')
    query = f"https://newsapi.org/v2/everything?q={search_string}&from={since_date}&pageSize=5&sortBy=popularity&apiKey={API_KEY_NEWS}"
    try:
        result = requests.get(query)
        return result.json()['articles']
    except:
        return []


def get_news(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    while True:
        if len(context.args) > 0:
            company_name = context.args[0]
            if len(context.args) > 1:
                try:
                    if int(context.args[1]) > 0:
                        delay = str(context.args[1])
                    else:
                        logger.info(f'Digit is non positive')
                        context.bot.send_message(chat_id=chat_id,
                                                 text=f"Второй аргумент <Количество дней> должно быть целым положительным числом.")
                        break
                except:
                    context.bot.send_message(chat_id=chat_id,
                                             text=f"Второй аргумент <Количество дней> должно быть целым положительным числом.")
                    break
            else:
                delay = '10'
            news_list = get_news_articles(company_name, int(delay))
            if len(news_list) == 0:
                logger.info(f'No news for search')
                context.bot.send_message(chat_id=chat_id,
                                         text=f"По запросу {company_name} не нашлось никаких новостей за последние {delay} дней.")
                break
            else:
                context.bot.send_message(chat_id=chat_id, text=f"Новости по вашему запросу за последние {delay} дней.")
                for news in news_list:
                    text = """Новость : {} \n 
                                  Ссылка : {} \n
                                  Опубликовано {} \n
                                  """.format(news['title'],
                                             news['url'],
                                             news['publishedAt'])

                    context.bot.send_message(chat_id=chat_id, text=text)

        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=f"Пожалуйста, введите название компании после команды /get_news")
        break

        
def get_prediction(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    today = datetime.datetime.today().strftime('%m/%d/%Y')
    lastweek = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime('%m/%d/%Y')
    tickers = []
    db_tickers = pd.read_csv(CSV_PATH + 'favorite_tickers.csv', index_col=0)
    while True:
        if len(context.args) > 0:
            if context.args[0] == 'favorite':
                for ticker in list(db_tickers[db_tickers['chat_id'] == chat_id]['ticker'].unique()):
                    tickers.append(ticker)
            else:
                tickers.append(context.args[0])
                try:
                    data = get_data(tickers[0], start_date=lastweek, end_date=today, index_as_date=True, interval="1d")
                except:
                    context.bot.send_message(chat_id=chat_id,
                                             text=f"Пожалуйста, введите корректное название тикера или слово favorite для ваших избранных акций.")
                    break
            if len(context.args) > 1:
                try:
                    if int(context.args[1]) > 0:
                        horizont = str(context.args[1])
                    else:
                        context.bot.send_message(chat_id=chat_id,
                                                 text=f"Второй аргумент <Количество дней> должно быть целым положительным числом.")
                        break
                except:
                    context.bot.send_message(chat_id=chat_id,
                                             text=f"Второй аргумент <Количество дней> должно быть целым положительным числом.")
                    break
            else:
                horizont = '30'
            for ticker in tickers:
                forecast = make_prediction(ticker, int(horizont))
                predicted_price = forecast.tail(1)['yhat'].values[0]
                current_price = forecast[forecast['y'].isna() == False].tail(1)['yhat'].values[0]
                price_change = round((predicted_price - current_price) / current_price * 100, 2)
                context.bot.send_message(chat_id=chat_id,
                                         text=f'Изменение цены {ticker} за {horizont} дней составит {price_change} %.')
                create_forecast_picture(forecast, ticker, horizont, chat_id)
                context.bot.send_photo(chat_id=chat_id,
                                       photo=open(f'{IMAGES_PATH}chat_{chat_id}_prediction_{ticker}.png', 'rb'))
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=f"Пожалуйста, введите название тикера после команды /get_prediction или слово favorite для ваших избранных акций.")
        break
        

def create_forecast_picture(forecast, ticker, horizont, chat_id):
    now = datetime.datetime.today()
    tmp = forecast[(forecast['ds'] > (now - datetime.timedelta(days=14)))]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot('ds', 'yhat_upper', data=tmp, marker='', color='blue', linewidth=2, linestyle='dashed', label="upper")
    ax.plot('ds', 'yhat_lower', data=tmp, marker='', color='blue', linewidth=2, linestyle='dashed', label="lower")
    ax.plot('ds', 'y', data=tmp, marker='', color='red', linewidth=2)
    ax.plot('ds', 'yhat', data=tmp, marker='o', color='blue', linewidth=3)
    ax.fill_between('ds', 'yhat_upper', 'yhat_lower', alpha=0.2, data=tmp)
    ax.set_title(f'Прогноз {ticker} на {horizont} дней вперед')
    plt.legend()
    plt.savefig(f'{IMAGES_PATH}chat_{chat_id}_prediction_{ticker}.png')


def main():
    updater = Updater(
        token=TOKEN,
        use_context=True
    )
    print(updater.bot.get_me())

    create_table()

    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(CommandHandler('find_ticker', find_ticker))
    updater.dispatcher.add_handler(CommandHandler('show_favorite_tickers', show_favorite_tickers))
    updater.dispatcher.add_handler(CommandHandler('add_new_ticker', add_new_ticker))
    updater.dispatcher.add_handler(CommandHandler('get_news', get_news))
    updater.dispatcher.add_handler(CommandHandler('delete_ticker', delete_ticker))
    updater.dispatcher.add_handler(CommandHandler('get_prediction', get_prediction))

    logging.info('Starting')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


# In[ ]:




