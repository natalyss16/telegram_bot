import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
import requests
import datetime 
from yahoo_fin.stock_info import get_data

API_KEY_STOCKS = '7d15a0d24a2f5bd2efd71c393a73cfff'
IMAGES_PATH = 'Media/'

def get_stock_data(ticker)->pd.DataFrame:
    """
    Returns daily stock data for last 365 days.
    """
    now = datetime.datetime.today().strftime('%m/%d/%Y')
    year_ago = (datetime.datetime.today()- datetime.timedelta(days=365)).strftime('%m/%d/%Y')
    
    df= get_data(ticker, start_date=year_ago, end_date=now, index_as_date = True, interval="1d")
    df['y'] = df['close']
    df.reset_index(inplace=True)
    df['ds'] = df['index']
    
    return df

def create_prophet_model()->Prophet:
        """
        Returns Prophet model
        """
        model = Prophet(weekly_seasonality=True,
                                  yearly_seasonality=True)
        model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
        return model
    
def train_prophet(train_df: pd.DataFrame):
    
    """
    Fits Prophet model
    ------------------
    train_df - pd.DataFrame with at least 2 columns:
    ds - pd.Series of data time in days
    y - value of exogenous variable
    ------------------
    Returns Prophet fitted model
    """
    model = create_prophet_model()
    model.fit(train_df)
    return model 

def make_prediction(ticker: str,  horizont_days: int)->pd.DataFrame:
    """
    Returns prediction for horizont_days
    ------------------
    ticker - ticker name
    horizont_days - number of periods to forecast in days
    ------------------
    """
    data = get_stock_data(ticker)
    model = train_prophet(data)
    future = model.make_future_dataframe(periods=horizont_days)
    forecast = model.predict(future)
    forecast = pd.merge(forecast, data[['ds', 'y']], on='ds', how='left')
    return forecast 

def create_forecast_picture(forecast, ticker, horizont, chat_id):
    now = datetime.datetime.today()
    tmp = forecast[(forecast['ds']>(now-datetime.timedelta(days=14)))]
    
    fig, ax = plt.subplots(figsize=(8,6))
    ax.plot( 'ds', 'yhat_upper', data=tmp, marker='', color='blue', linewidth=2, linestyle='dashed', label="upper")
    ax.plot( 'ds', 'yhat_lower', data=tmp, marker='', color='blue', linewidth=2, linestyle='dashed', label="lower")
    ax.plot( 'ds', 'y', data=tmp, marker='', color='red', linewidth=2)
    ax.plot( 'ds', 'yhat', data=tmp, marker='o', color='blue', linewidth=3)
    ax.fill_between('ds', 'yhat_upper', 'yhat_lower', alpha=0.2,  data=tmp)
    ax.set_title(f'Прогноз {ticker} на {horizont} дней вперед')
    plt.legend()
    plt.savefig(f'{IMAGES_PATH}chat_{chat_id}_prediction_{ticker}.png')
    

