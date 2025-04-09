import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
import stocks
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import yfinance as yf
import configparser
import os
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter

class StockAnalysisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.configure(bg='#1e1e1e')
        self.figure = plt.Figure(figsize=(10, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.live_update = tk.BooleanVar(value=False)
        self.update_interval_var = tk.IntVar(value=5)
        self.degree_var = tk.IntVar(value=3)
        self.dark_mode = tk.BooleanVar(value=False)
        self.time_range_var = tk.StringVar(value="5Y")
        self.last_price = None

        self.title("Stock Analysis")
        self.geometry('1920x1080')

        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TButton",
                        foreground="white",
                        background="#3a3a3a",
                        font=("Segoe UI", 10, "bold"),
                        padding=10,
                        borderwidth=1
                        )

        style.map("TButton",
                  background=[("active", "#505050"), ("pressed", "#282828")],
                  relief=[("pressed", "sunken"), ("!pressed", "raised")]
                  )

        style.configure("TCheckbutton",
                        foreground="black",
                        font=("Segoe UI", 10),
                        )

        style.map("TCheckbutton",
                  foreground=[("active", "black")],
                  indicatorcolor=[("selected", "#00cc66")]
                  )

        style.configure("TLabel",
                        font=("Segoe UI", 10),
                        foreground="black"
                        )

        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=4, column=0, columnspan=4, sticky="nsew")
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.toolbar_frame.grid(row=5, column=0, columnspan=4, sticky="ew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        self.news_frame = ttk.LabelFrame(self.main_frame, text="Headlines", padding=10)
        self.news_frame.grid(row=0, column=4, rowspan=6, sticky="nsew", padx=(10,0))

        self.news_text = tk.Text(self.news_frame, wrap=tk.WORD, width=50, height=30, font=("Segoe UI", 9))
        self.news_text.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(self.main_frame, text="Stock Input")
        input_frame.grid(row=0, column=0, columnspan=4, pady=10, sticky="ew")

        ttk.Label(input_frame, text="Ticker:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticker_entry = ttk.Entry(input_frame, width=10)
        self.ticker_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ticker_entry.insert(0, 'AAPL')

        ttk.Label(input_frame, text="Time Range:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.time_range_combo = ttk.Combobox(input_frame, textvariable=self.time_range_var, values=["1M", "3M", "6M", "1Y", "3Y", "5Y"], state="readonly", width=10)
        self.time_range_combo.set("6M")
        self.time_range_combo.grid(row=1, column=1, padx=5, pady=5)
        self.time_range_combo.bind("<<ComboboxSelected>>", lambda e: self.update_chart())

        self.price_label = tk.Label(self.main_frame, text="Price: $0.00", font=("Segoe UI", 18, "bold"), width=20, height=2)
        self.price_label.grid(row=3, column=0, columnspan=4, pady=(10, 20))

        end_date = datetime.today()
        self.start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        self.end_date = end_date.strftime('%Y-%m-%d')

        button_frame = ttk.LabelFrame(self.main_frame, text="Actions")
        button_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky="ew")

        ttk.Button(button_frame, text="Process", command=self.process_stock).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="Export Result", command=self.export_results).grid(row=0, column=1, padx=10,
                                                                                         pady=10)
        ttk.Button(button_frame, text="Settings", command=self.open_settings).grid(row=0, column=2, padx=10, pady=10)

        ttk.Button(button_frame, text="Regression", command=self.show_regression).grid(row=1, column=0, padx=10,
                                                                                       pady=10)
        ttk.Button(button_frame, text="Polynomial Regression", command=self.show_polynomial_regression).grid(row=1,
                                                                                                             column=1,
                                                                                                             padx=10,
                                                                                                             pady=10)
        ttk.Label(button_frame, text="Degree:").grid(row=1, column=2, padx=5)
        ttk.Button(button_frame, text="Stock Graph", command=self.show_stock_graph).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="RSI", command=self.RSI).grid(row=2, column=1, padx=10, pady=10)
        ttk.Button(button_frame, text="MACD", command=self.MACD).grid(row=2, column=2, padx=10, pady=10)
        ttk.Button(button_frame, text="Bollinger", command=self.boll).grid(row=2, column=3, padx=10, pady=10)

        self.degree_spinbox = ttk.Spinbox(button_frame, from_=1, to=10, textvariable=self.degree_var, width=5)
        self.degree_spinbox.grid(row=1, column=3, padx=5)

        self.live_checkbox = ttk.Checkbutton(button_frame, text="Live Update", variable=self.live_update)
        self.live_checkbox.grid(row=3, column=0, padx=10, pady=10)
        ttk.Label(button_frame, text="Interval (s):").grid(row=3, column=1, padx=5)
        self.interval_label = ttk.Label(button_frame, text="5s")
        self.interval_label.grid(row=3, column=4, padx=5)

        ttk.Scale(button_frame, from_=1, to=60, variable=self.update_interval_var,
                  orient=tk.HORIZONTAL, command=self.update_interval_display).grid(row=3, column=2, columnspan=2,
                                                                                   sticky="ew", padx=10)

        self.analysis_frame = ttk.LabelFrame(self.main_frame, text="Analysis", padding=10)
        self.analysis_frame.grid(row=0, column=5, rowspan=6, sticky="nsew", padx=(10, 0))

        self.analysis_labels = []
        metric_names = ["RSI Norm", "MACD Norm", "Bollinger Norm", "Sentiment Norm", "Total Score", "Trend"]
        for name in metric_names:
            label = tk.Label(self.analysis_frame, text=f"{name}: --", font=("Segoe UI", 11, "bold"), anchor="w")
            label.pack(anchor="w", padx=10, pady=2)
            self.analysis_labels.append(label)

        self.action_label = tk.Label(self.analysis_frame, text="Awaiting Analysis...", font=("Segoe UI", 24, "bold"),
                                     fg="gray")
        self.action_label.pack(pady=15)
        placeholder_fig = plt.Figure(figsize=(5, 3))
        ax = placeholder_fig.add_subplot(111)
        ax.set_title("Prediction Preview")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(True)

        self.prediction_canvas = None
        self.last_result = None
        self.display_headlines = tk.BooleanVar()
        self.auto_refresh = tk.BooleanVar()
        self.live_update = tk.BooleanVar()
        self.interval_var = tk.StringVar()
        self.load_settings()
        self.update_chart()

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("300x250")
        style = ttk.Style(settings_window)
        style.theme_use('clam')
        ttk.Label(settings_window, text="Display Options", font=("Segoe UI", 12, "bold")).pack(pady=10)

        ttk.Checkbutton(
            settings_window,
            text="Show Headlines",
            variable=self.display_headlines
        ).pack(anchor="w", padx=20)

        ttk.Checkbutton(
            settings_window,
            text="Enable Live Graph Update",
            variable=self.live_update
        ).pack(anchor="w", padx=20)

        ttk.Checkbutton(
            settings_window,
            text="Price Display",
            variable=self.auto_refresh
        ).pack(anchor="w", padx=20)



        ttk.Label(settings_window, text="Fetch Interval:").pack(pady=(10, 0))
        ttk.Combobox(settings_window, textvariable=self.interval_var, values=["1m", "5m", "15m", "30m", "1h", "1d"]).pack()
        ttk.Button(
            settings_window,
            text="Save Settings",
            command=lambda: self.save_settings(settings_window)
        ).pack(pady=20)

    def save_settings(self, window=None):
        config = configparser.ConfigParser()
        config["Options"] = {
            "show_headlines": str(self.display_headlines.get()),
            "live_update": str(self.live_update.get()),
            "auto_refresh": str(self.auto_refresh.get()),
            "interval": str(self.interval_var.get())
        }
        with open("user_settings.inf", "w") as configfile:
            config.write(configfile)
        if window:
            window.destroy()

    def load_settings(self):
        config = configparser.ConfigParser()
        if os.path.exists("user_settings.inf"):
            config.read("user_settings.inf")
            self.display_headlines.set(config.getboolean("Options", "show_headlines", fallback=True))
            self.live_update.set(config.getboolean("Options", "live_update", fallback=False))
            self.auto_refresh.set(config.getboolean("Options", "auto_refresh", fallback=True))
            self.interval_var.set(config.get("Options", "interval", fallback='1h'))
        else:
            self.display_headlines.set(True)
            self.live_update.set(False)
            self.auto_refresh.set(True)
            self.interval_var.set('1h')

    def show_stock_graph(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))

        if data.empty:
            messagebox.showerror("Data Error", "No data available for the selected period.")
            return

        data = data[['Open', 'High', 'Low', 'Close']].dropna().reset_index()
        data['FormattedDate'] = data['Datetime'].dt.strftime('%Y-%m-%d')

        data['Index'] = range(len(data))
        ohlc = data[['Index', 'Open', 'High', 'Low', 'Close']].values

        self.ax.clear()
        candlestick_ohlc(self.ax, ohlc, width=0.6, colorup='green', colordown='red')

        self.ax.set_xticks(data['Index'][::max(len(data) // 10, 1)])
        self.ax.set_xticklabels(data['FormattedDate'][::max(len(data) // 10, 1)], rotation=45, ha='right')

        self.ax.grid(True)
        self.ax.set_title(f'{ticker} Candlestick Chart')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Price')

        self.canvas.draw()

    def update_prediction_plot(self, fig):
        if self.prediction_canvas:
            self.prediction_canvas.get_tk_widget().destroy()
        self.prediction_canvas = FigureCanvasTkAgg(fig, master=self.analysis_frame)
        self.prediction_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.prediction_canvas.draw()

    def display_analysis_results(self, result):
        metric_values = [
            result[0],
            result[1],
            result[2],
            result[3],
            result[4],
            result[5]
        ]

        for i, value in enumerate(metric_values):
            text = f"{self.analysis_labels[i].cget('text').split(':')[0]}: {value:.2f}" if isinstance(value,
                                                                                                      float) else f"{self.analysis_labels[i].cget('text').split(':')[0]}: {value}"
            color = "green" if isinstance(value, (int, float)) and value >= 0 else "red"
            self.analysis_labels[i].config(text=text, fg=color)

        if result[4] >= 0:
            self.action_label.config(text="BUY", fg="green")
        else:
            self.action_label.config(text="SHORT", fg="red")

    def update_canvas(self, new_figure):
        self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(new_figure, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=4, column=0, columnspan=4, sticky="nsew")
        self.canvas.draw()
        self.toolbar.destroy()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

    def process_stock(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        if isinstance(data['Close'], pd.DataFrame):
            data['Close'] = data['Close'].squeeze()
        analysis_result = stocks.predict_stock_movement(data, ticker)
        self.last_result = {
            'Ticker': ticker,
            'Start Date': start_date,
            'End Date': end_date.strftime('%Y-%m-%d'),
            'RSI Norm': analysis_result[0],
            'MACD Norm': analysis_result[1],
            'Bollinger Position Norm': analysis_result[2],
            'Sentiment Norm': analysis_result[3],
            'Total Score': analysis_result[4],
            'Trend': analysis_result[5]
        }
        self.display_analysis_results(analysis_result)
        self.show_stock_graph()
        if self.display_headlines.get():
            self.display_headlines_sentiment()
        if self.auto_refresh.get():
            self.update_price_display()
        fig = stocks.plot_projection(data, ticker, return_fig=True)
        self.update_prediction_plot(fig)



    def calculate_start_date(self, range_str, end_date):
        today = end_date
        if range_str == "1M":
            return (today - timedelta(days=30)).strftime('%Y-%m-%d')
        elif range_str == "3M":
            return (today - timedelta(days=90)).strftime('%Y-%m-%d')
        elif range_str == "6M":
            return (today - timedelta(days=180)).strftime('%Y-%m-%d')
        elif range_str == "1Y":
            return (today - timedelta(days=365)).strftime('%Y-%m-%d')
        elif range_str == "3Y":
            return (today - timedelta(days=3*365)).strftime('%Y-%m-%d')
        else:
            return (today - timedelta(days=5*365)).strftime('%Y-%m-%d')

    def update_interval_display(self, val):
        self.interval_label.config(text=f"{int(float(val))}s")

    def update_price_display(self):
        ticker = self.ticker_entry.get()

        live_data = yf.Ticker(ticker).history(period="1d", interval="1m")
        current_price = live_data['Close'].iloc[-1]
        print(current_price)
        color = "green" if self.last_price is not None and current_price > self.last_price else "red"
        self.price_label.config(text=f"Price: ${current_price:.2f}", bg=color, fg="white")
        self.last_price = current_price


    def update_chart(self):
        ticker = self.ticker_entry.get()
        if not stocks.is_market_open(ticker):
            self.live_checkbox.state(["disabled"])
            self.live_update.set(False)
        else:
            self.live_checkbox.state(["!disabled"])

        if self.live_update.get():
            self.show()
            self.update_price_display()

        interval_ms = self.update_interval_var.get() * 1000
        self.after(interval_ms, self.update_chart)


    def draw_secondary_plot(self, title, y_data, label):
        self.ax.clear()
        self.ax.plot(y_data.index, y_data, label=label)
        self.ax.set_title(title)
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel(label)
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()

    def RSI(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        stocks.rsi(data)
        self.ax.clear()
        self.ax.plot(data.index, data['RSI'], color='purple', label='RSI')
        self.ax.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        self.ax.axhline(30, color='green', linestyle='--', label='Oversold (30)')
        self.ax.set_title(f'{ticker} RSI')
        self.ax.set_ylim(0, 100)
        self.ax.grid()
        self.ax.legend()
        self.canvas.draw()

    def MACD(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        stocks.macd(data)
        macd_hist = data['MACD'] - data['MACD Signal']
        colors = ['green' if val >= 0 else 'red' for val in macd_hist]
        self.ax.clear()
        self.ax.plot(data.index, data['MACD'], color='blue', label='MACD Line')
        self.ax.plot(data.index, data['MACD Signal'], color='orange', label='Signal Line')
        self.ax.bar(data.index, macd_hist, color=colors, alpha=0.5, label='MACD Histogram')
        self.ax.set_title(f'{ticker} MACD')
        self.ax.grid()
        self.ax.legend()
        self.canvas.draw()

    def boll(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        stocks.bollinger_bands(data)
        self.ax.clear()
        self.ax.plot(data.index, data['Close'], label='Close')
        self.ax.plot(data.index, data['Upper Band'], label='Upper Band', linestyle='--')
        self.ax.plot(data.index, data['Lower Band'], label='Lower Band', linestyle='--')
        self.ax.set_title(f'{ticker} Bollinger Bands')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Price')
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()

    def predict_graph(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        stocks.moving_averages(data)
        stocks.bollinger_bands(data)
        stocks.rsi(data)
        stocks.plot_projection(data, ticker)

    def analyze_stock(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        if isinstance(data['Close'], pd.DataFrame):
            data['Close'] = data['Close'].squeeze()
        analysis_result = stocks.predict_stock_movement(data, ticker)
        self.last_result = {
            'Ticker': ticker,
            'Start Date': start_date,
            'End Date': end_date.strftime('%Y-%m-%d'),
            'RSI Norm': analysis_result[0],
            'MACD Norm': analysis_result[1],
            'Bollinger Position Norm': analysis_result[2],
            'Sentiment Norm': analysis_result[3],
            'Total Score': analysis_result[4],
            'Trend': analysis_result[5]
        }
        self.display_results(analysis_result)

    def export_results(self):
        if self.last_result is None:
            messagebox.showinfo("No Result", "Run an analysis first.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            df = pd.DataFrame([self.last_result])
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Exported", f"Results saved to {file_path}")

    def display_results(self, analysis_result):
        result_window = tk.Toplevel()
        result_window.title("Analysis Results")
        result_window.geometry("400x350")
        labels = [
            f"RSI Norm: {analysis_result[0]}",
            f"MACD Norm: {analysis_result[1]}",
            f"Bollinger Position Norm: {analysis_result[2]}",
            f"Sentiment Norm: {analysis_result[3]}",
            f"Total Score: {analysis_result[4]}",
            f"Trend: {analysis_result[5]}"
        ]
        for text in labels:
            label = tk.Label(result_window, text=text, font=("Segoe UI", 10))
            label.pack(pady=5)
        score_label = result_window.winfo_children()[-2]
        score_label.config(fg="green" if analysis_result[4] >= 0 else "red")

    def display_headlines_sentiment(self):
        ticker = self.ticker_entry.get()
        headlines_sentiment = stocks.show_headlines(ticker)
        self.news_text.delete(1.0, tk.END)
        if headlines_sentiment:
            with open("news_cache.txt", "w", encoding="utf-8") as f:
                for idx, (headline, sentiment) in enumerate(headlines_sentiment, 1):
                    f.write(f"{idx}. {headline} - Sentiment: {sentiment:.2f}\n")
            with open("news_cache.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if ' - Sentiment:' in line:
                    headline, sentiment = line.split(' - Sentiment:')
                    formatted = f"• {headline.strip()}\n   Sentiment Score: {sentiment.strip()}\n{'-'*60}\n"
                    self.news_text.insert(tk.END, formatted)
        else:
            self.news_text.delete(1.0, tk.END)
            self.news_text.insert(tk.END, "No headlines found for this stock.")

    def show_regression(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        result = stocks.linear_regression_trend(data)
        self.ax.clear()
        self.ax.plot(result['Datetime'], result['Close'], label='Close Price')
        self.ax.plot(result['Datetime'], result['LR Trend'], label='Linear Regression', linestyle='--')
        self.ax.set_title(f'{ticker} Linear Regression Trend')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Price')
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

    def show_polynomial_regression(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        result = stocks.polynomial_regression_trend(data, degree=self.degree_var.get())
        self.ax.clear()
        self.ax.plot(result['Datetime'], result['Close'], label='Close Price')
        self.ax.plot(result['Datetime'], result['Poly Trend'], label=f'Polynomial Regression (deg={self.degree_var.get()})', linestyle='--')
        self.ax.set_title(f'{ticker} Polynomial Regression Trend')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Price')
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

if __name__ == "__main__":
    app = StockAnalysisApp()
    app.mainloop()