# stock-analysis-tool
## Features
- Fetch stock data from Yahoo Finance using `yfinance`.
- Calculate and visualize technical indicators:
  - Moving Averages (20 day, 50 day)
  - Bollinger Bands
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD) + Signal Line
- Perform sentiment analysis on news headlines related to the stock using `TextBlob`, appends to a file acting like a cache.
- Includes linear and polynomial regression-based price projections with customizable degree selection using `Sklearn`
- Display stock data, technical indicators, sentiment analysis results, and price predictions through a user-friendly GUI using `tkinter`.
- Live stock data updates are available only when the respective market is open (limited to major markets for now).
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
- pytz
- pandas_market_calendars

**Usage:** 
Ensure you have all the dependencies installed. You can do this by running `python dependencies.py`.

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Run `python dependencies.py` to launch the GUI.
4. Run `python gui.py` to launch the GUI.
5. Enter the stock ticker symbol & the period
6. Click "Process" to initialise a stock. You can use the other buttons to change the graph views.

![image](https://github.com/user-attachments/assets/cbf33fe2-bd54-414c-8066-88a19744505b)

**v0.1 Update:**
- Added a Settings Page allowing users to customize the Process .
- You can now disable headline sentiment analysis, toggle auto-refresh of the price & graph, and adjust the stock data fetch interval.
- Preferences are saved to a .inf configuration file.

