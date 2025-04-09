import yfinance as yf
import pandas as pd
import ta
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import pandas_market_calendars as mcal
from datetime import datetime
import pytz
import random
def is_market_open(ticker):
    try:
        info = yf.Ticker(ticker).info
        exchange = info.get("exchange", "").upper()

        exchange_lookup = {
            "NASDAQ": "NASDAQ",
            "NMS": "NASDAQ",
            "NYSE": "NYSE",
            "NYQ": "NYSE",
            "LSE": "LSE",
            "TSX": "TSX",
            "TOR": "TSX",
        }

        asian_exchanges = {
            "JPX": ("Asia/Tokyo", 9, 15),
            "TSE": ("Asia/Tokyo", 9, 15),
            "HKG": ("Asia/Hong_Kong", 9, 16),
            "SHG": ("Asia/Shanghai", 9, 15),
            "SHE": ("Asia/Shanghai", 9, 15),
        }

        if exchange in asian_exchanges:
            tz_str, open_hr, close_hr = asian_exchanges[exchange]
            tz = pytz.timezone(tz_str)
            now = datetime.now(tz)
            return now.hour >= open_hr and now.hour < close_hr

        cal_code = exchange_lookup.get(exchange)
        if not cal_code:
            return False

        cal = mcal.get_calendar(cal_code)
        today = datetime.now().strftime('%Y-%m-%d')
        sched = cal.schedule(start_date=today, end_date=today)

        if sched.empty:
            return False

        aware_now = pytz.utc.localize(datetime.utcnow())
        open_time = sched.iloc[0]['market_open']
        close_time = sched.iloc[0]['market_close']

        return open_time <= aware_now <= close_time
    except Exception as e:
        print(f"ERROR {e}")
        return False


def getNewsData(stock):
    url = f"https://finviz.com/quote.ashx?t={stock}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="fullview-news-outer")
    news_results = []
    if table:
        rows = table.find_all("tr")
        for row in rows:
            timestamp = row.td.text.strip()
            link_tag = row.find_all("td")[1].find("a")
            title = link_tag.text.strip()
            link = link_tag["href"]
            news_results.append({
                "link": link,
                "title": title,
                "snippet": "",
                "date": timestamp,
                "source": "Finviz"
            })
    return news_results

def get_headlines_sentiment(stock):
    news_data = getNewsData(stock)
    headlines = [item['title'] for item in news_data]
    if not headlines:
        return None
    sentiment_scores = [TextBlob(headline).sentiment.polarity for headline in headlines]
    sentiment_scores = [score for score in sentiment_scores if score != 0]
    if not sentiment_scores:
        return None
    average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    rating = 5.5 + 4.5 * (average_sentiment / 2)
    return rating

def show_headlines(stock):
    news_data = getNewsData(stock)
    headlines = [item['title'] for item in news_data]
    if not headlines:
        return None
    sentiment_scores = [TextBlob(headline).sentiment.polarity for headline in headlines]
    headlines_with_sentiment = list(zip(headlines, sentiment_scores))
    return headlines_with_sentiment

def fetch_stock_data(ticker, start_date, end_date):
    try:
        with open("user_settings.inf", "r") as f:
            lines = f.readlines()
            interval_line = [line for line in lines if line.startswith("interval =")]
            interval = interval_line[0].split("=")[1].strip() if interval_line else "1h"
    except:
        interval = "15m"

    data = yf.download(ticker, interval=interval, start=start_date, end=end_date)
    if data.empty:
        return data
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    data = data.astype(float)
    print(data)
    return data

def moving_averages(data):
    data['20-day MA'] = data['Close'].rolling(window=20).mean()
    data['50-day MA'] = data['Close'].rolling(window=50).mean()

def bollinger_bands(data):
    data['20-day Mean'] = data['Close'].rolling(window=20).mean()
    data['20-day STD'] = data['Close'].rolling(window=20).std()
    data['Upper Band'] = data['20-day Mean'] + (data['20-day STD'] * 2)
    data['Lower Band'] = data['20-day Mean'] - (data['20-day STD'] * 2)

def rsi(data):
    close_series = data['Close']
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.squeeze()
    rsi_indicator = ta.momentum.RSIIndicator(close_series)
    data['RSI'] = rsi_indicator.rsi()
    return data['RSI']

def macd(data):
    close_series = data['Close']
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.squeeze()
    macd_calc = ta.trend.MACD(close_series)
    data['MACD'] = pd.Series(np.ravel(macd_calc.macd()), index=data.index)
    data['MACD Signal'] = pd.Series(np.ravel(macd_calc.macd_signal()), index=data.index)
    return data['MACD']

def detect_trend(data):
    if len(data) < 50:
        return "Not enough data"
    ma_short = data['20-day MA'].iloc[-1]
    ma_long = data['50-day MA'].iloc[-1]
    if ma_short > ma_long:
        return "Bullish"
    elif ma_short < ma_long:
        return "Bearish"
    return "Sideways"

def showboll(data, ticker):
    ohlc_data = data[['Open', 'High', 'Low', 'Close']].astype(float)
    ohlc_data.reset_index(inplace=True)
    ohlc_data.rename(columns={'index': 'Datetime'}, inplace=True)
    if 'Datetime' not in ohlc_data.columns:
        for col in ohlc_data.columns:
            if np.issubdtype(ohlc_data[col].dtype, np.datetime64):
                ohlc_data.rename(columns={col: 'Datetime'}, inplace=True)
                break
    ohlc_data['Datetime'] = mdates.date2num(ohlc_data['Datetime'].dt.to_pydatetime())
    fig, axs = plt.subplots()
    candlestick_ohlc(axs, ohlc_data.values, width=0.6, colorup='green', colordown='red')
    axs.plot(mdates.date2num(data.index.to_pydatetime()), data['Upper Band'], color='orange', label='Upper Band')
    axs.plot(mdates.date2num(data.index.to_pydatetime()), data['Lower Band'], color='green', label='Lower Band')
    axs.set_title(f'{ticker} Bollinger Bands')
    axs.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    axs.legend()
    axs.tick_params(axis='x', rotation=45)
    axs.grid()
    plt.tight_layout()
    plt.show()

def showgraph(data):
    ohlc_data = data[['Open', 'High', 'Low', 'Close']].astype(float)
    ohlc_data.reset_index(inplace=True)
    ohlc_data['Datetime'] = mdates.date2num(ohlc_data['Datetime'].dt.to_pydatetime())
    fig, axs = plt.subplots()
    candlestick_ohlc(axs, ohlc_data.values, width=0.6, colorup='green', colordown='red')
    axs.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    axs.legend()
    axs.tick_params(axis='x', rotation=45)
    axs.grid()
    plt.tight_layout()
    plt.show()

def showRSI(data, ticker):
    fig, axs = plt.subplots()
    axs.plot(data.index, data['RSI'], color='purple', label='RSI')
    axs.axhline(70, color='red', linestyle='--', label='Overbought (70)')
    axs.axhline(30, color='green', linestyle='--', label='Oversold (30)')
    axs.set_title(f'{ticker} RSI')
    axs.set_ylim(0, 100)
    axs.grid()
    axs.legend()
    plt.tight_layout()
    plt.show()

def linear_regression_trend(data):
    data = data.dropna()
    data = data.reset_index()
    data['Timestamp'] = data['Datetime'].map(lambda x: x.toordinal())
    X = data[['Timestamp']]
    y = data['Close']
    model = LinearRegression()
    model.fit(X, y)
    data['LR Trend'] = model.predict(X)
    return data[['Datetime', 'Close', 'LR Trend']]

def polynomial_regression_trend(data, degree=2):
    degree = int(degree)
    data = data.dropna().reset_index()
    if 'Datetime' not in data.columns:
        data['Datetime'] = data['index']
    data['Timestamp'] = data['Datetime'].map(lambda x: x.toordinal())
    X = data[['Timestamp']]
    y = data['Close']

    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X)

    model = LinearRegression()
    model.fit(X_poly, y)

    data['Poly Trend'] = model.predict(X_poly)
    return data[['Datetime', 'Close', 'Poly Trend']]

def showMACD(data, ticker):
    fig, axs = plt.subplots()
    axs.plot(data.index, data['MACD'], color='blue', label='MACD Line')
    axs.plot(data.index, data['MACD Signal'], color='orange', label='Signal Line')
    histogram = data['MACD'] - data['MACD Signal']
    colors = ['green' if val >= 0 else 'red' for val in histogram]
    axs.bar(data.index, histogram, color=colors, alpha=0.5, label='MACD Histogram')
    axs.set_title(f'{ticker} MACD')
    axs.grid()
    axs.legend()
    plt.tight_layout()
    plt.show()

def predict_stock_movement(data, ticker):
    for col in ['Close', 'Open', 'High', 'Low']:
        if isinstance(data[col], pd.DataFrame):
            data[col] = data[col].squeeze()
    close_series = data['Close'].squeeze()
    data['20-day MA'] = close_series.rolling(window=20).mean()
    data['50-day MA'] = close_series.rolling(window=50).mean()
    bollinger = ta.volatility.BollingerBands(close_series)
    data['Upper Band'] = pd.Series(np.ravel(bollinger.bollinger_hband()), index=data.index)
    data['Middle Band'] = pd.Series(np.ravel(bollinger.bollinger_mavg()), index=data.index)
    data['Lower Band'] = pd.Series(np.ravel(bollinger.bollinger_lband()), index=data.index)
    rsi = ta.momentum.RSIIndicator(close_series)
    data['RSI'] = pd.Series(np.ravel(rsi.rsi()), index=data.index)
    macd = ta.trend.MACD(close_series)
    data['MACD'] = pd.Series(np.ravel(macd.macd()), index=data.index)
    data['MACD Signal'] = pd.Series(np.ravel(macd.macd_signal()), index=data.index)
    latest_data = data.dropna().iloc[-1]
    sentiment_rating = get_headlines_sentiment(ticker)
    rsi_norm = ((latest_data['RSI'] - 50) / 50)
    macd_diff_val = latest_data['MACD'] - latest_data['MACD Signal']
    macd_diff_val = macd_diff_val.iloc[0] if isinstance(macd_diff_val, pd.Series) else macd_diff_val
    macd_max = max(abs(macd_diff_val), 1)
    macd_norm = macd_diff_val / macd_max
    middle_band = latest_data['Middle Band']
    close_price = latest_data['Close']
    band_width = latest_data['Upper Band'] - latest_data['Lower Band']
    band_width = band_width.iloc[0] if isinstance(band_width, pd.Series) else band_width
    band_width_max = max(band_width, 1)
    bollinger_position_norm = (close_price - middle_band) / (band_width_max / 2)
    if isinstance(bollinger_position_norm, pd.Series):
        bollinger_position_norm = bollinger_position_norm.iloc[0]
    elif isinstance(bollinger_position_norm, np.ndarray):
        bollinger_position_norm = bollinger_position_norm.item()
    bollinger_position_norm = float(bollinger_position_norm)
    sentiment_norm = ((sentiment_rating - 5) / 5) if sentiment_rating is not None else 0
    weighted_sum = (
        0.33 * rsi_norm +
        0.33 * macd_norm +
        0.33 * sentiment_norm
    )
    score = 50 * weighted_sum
    trend = detect_trend(data)
    return (
        float(rsi_norm.iloc[0] if isinstance(rsi_norm, pd.Series) else rsi_norm),
        float(macd_norm),
        float(bollinger_position_norm),
        float(sentiment_norm),
        float(score),
        trend
    )

def plot_projection(data, ticker, return_fig=False):
    recent_slope = (data['50-day MA'].iloc[-1] - data['50-day MA'].iloc[-50]) / 50
    future_days = np.arange(1, 31)
    future_prices = data['50-day MA'].iloc[-1] + recent_slope * future_days
    fig = plt.figure(figsize=(5, 3))
    plt.plot(data.index, data['Close'], label='Actual Prices')
    plt.plot(data.index, data['50-day MA'], label='50-day MA')
    future_dates = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=30)
    plt.plot(future_dates, future_prices, label='Projected', linestyle='dashed')
    plt.legend()
    plt.title(f'{ticker} Projection')
    plt.grid(True)
    plt.tight_layout()
    if return_fig:
        return fig
    plt.show()
