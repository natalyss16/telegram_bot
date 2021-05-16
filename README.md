# stonks_bot
Бот, который умеет предсказывать изменение цен акций, а также собирать новости по компаниям

[Ссылка на бот](https://t.me/HSE_stonks_bot)

Использованные API: [Yahoo Finance](https://finance.yahoo.com/quotes/API,Documentation/view/v1/), [News API](https://newsapi.org/)

`start_handler` функция приветствия

`find_companies` и `find_ticker` ищут тикер по названию компании

arg: имя компании

`add_new_ticker` добавляет тикер в список избранных

arg: название тикера

`create_table` создает таблицу из избранных тикеров

`show_favorite_tickers` выводит список избранных тикеров

`delete_ticker` удаляет тикер из списка избранного

arg: название тикера

`get_news_articles` и `get_news` показывает новости по выбранной компании

args: название компании, количество дней

default: 10 дней

`get_prediction` предсказывает изменение цены акции с использованием модели [prophet](https://facebook.github.io/prophet/)

arg: название тикера / favorite, количество дней

default: 30 дней

`create_forecast_picture` создает график изменения цены акции
