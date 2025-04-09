# stock-analysis-tool
A user-friendly stock analysis toolkit built in Python. This app provides a clean graphical interface for fetching stock data, computing technical indicators, analyzing news sentiment, and visualizing market trends.

## Features
- Fetch stock data from Yahoo Finance using `yfinance`.
- Calculate and visualize technical indicators:
  - Moving Averages (20 day, 50 day)
  - Bollinger Bands
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD) + Signal Line
- Perform sentiment analysis on news headlines related to the stock using `TextBlob`.
- Includes linear and polynomial regression-based price projections with customizable degree selection using `Sklearn`
- Display stock data, technical indicators, sentiment analysis results, and price predictions through a user-friendly GUI using `tkinter`.
- Evaluate the buying, holding, or selling recommendation based on the analysis and predictions.

## Dependencies 
- Python 3.x 
- pandas
- yfinance
- matplotlib
- ta
- requests
- bs4
- textblob
- numpy
- mplfinance
- scikit-learn
- tkinter


 
**Usage:** 
Ensure you have all the dependencies installed. 

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Run `python dependencies.py` to launch the GUI.
4. Run `python gui.py` to launch the GUI.
5. Enter the stock ticker symbol, start date, and end date.
6. Click the buttons to fetch data, calculate and visualize technical indicators, perform sentiment analysis, and view the price predictions along with a recommendation for buying, holding, or selling the stock.
