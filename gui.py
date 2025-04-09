import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
import stocks
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk


class StockAnalysisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.figure = plt.Figure(figsize=(10, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.live_update = tk.BooleanVar(value=False)
        self.update_interval_var = tk.IntVar(value=5)
        self.degree_var = tk.IntVar(value=3)
        self.dark_mode = tk.BooleanVar(value=False)
        self.time_range_var = tk.StringVar(value="5Y")

        self.title("Stock Analysis")
        self.geometry('1400x1000')

        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))

        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=4, column=0, columnspan=4, sticky="nsew")
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.toolbar_frame.grid(row=5, column=0, columnspan=4, sticky="ew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().grid(row=4, column=0, columnspan=4, sticky="nsew")
        self.news_frame = ttk.LabelFrame(self.main_frame, text="Headlines", padding=10)
        self.news_frame.grid(row=0, column=4, rowspan=5, sticky="nsew", padx=(10,0))

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

        end_date = datetime.today()
        self.start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        self.end_date = end_date.strftime('%Y-%m-%d')

        button_frame = ttk.LabelFrame(self.main_frame, text="Actions")
        button_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky="ew")

        ttk.Button(button_frame, text="Show Graph", command=self.show).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="Bollinger", command=self.boll).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(button_frame, text="RSI", command=self.RSI).grid(row=0, column=2, padx=10, pady=10)
        ttk.Button(button_frame, text="MACD", command=self.MACD).grid(row=0, column=3, padx=10, pady=10)
        ttk.Button(button_frame, text="Predict Graph", command=self.predict_graph).grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="Predict", command=self.analyze_stock).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(button_frame, text="Export Result", command=self.export_results).grid(row=1, column=2, padx=10, pady=10)
        ttk.Button(button_frame, text="Regression", command=self.show_regression).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="Polynomial Regression", command=self.show_polynomial_regression).grid(row=2, column=1, padx=10, pady=10)
        ttk.Label(button_frame, text="Degree:").grid(row=2, column=2, padx=5)
        self.degree_spinbox = ttk.Spinbox(button_frame, from_=1, to=10, textvariable=self.degree_var, width=5)
        self.degree_spinbox.grid(row=2, column=3, padx=5)

        self.live_checkbox = ttk.Checkbutton(button_frame, text="Live Update", variable=self.live_update)
        self.live_checkbox.grid(row=3, column=0, padx=10, pady=10)
        ttk.Label(button_frame, text="Interval (s):").grid(row=3, column=1, padx=5)
        self.interval_label = ttk.Label(button_frame, text="5s")
        self.interval_label.grid(row=3, column=4, padx=5)

        ttk.Scale(button_frame, from_=1, to=60, variable=self.update_interval_var,
                  orient=tk.HORIZONTAL, command=self.update_interval_display).grid(row=3, column=2, columnspan=2,
                                                                                   sticky="ew", padx=10)

        self.last_result = None
        self.update_chart()

    def show(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        self.ax.clear()
        self.ax.plot(data.index, data['Close'], label='Close Price')
        self.ax.set_title(f'{ticker} Stock Price')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Price')
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()
        self.display_headlines_sentiment()

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

    def update_chart(self):
        ticker = self.ticker_entry.get()
        if not stocks.is_market_open(ticker):
            self.live_checkbox.state(["disabled"])
            self.live_update.set(False)
        else:
            self.live_checkbox.state(["!disabled"])

        if self.live_update.get():
            self.show()

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
        rsi_data = stocks.rsi(data)
        self.draw_secondary_plot(f'{ticker} RSI', rsi_data, 'RSI')

    def MACD(self):
        ticker = self.ticker_entry.get()
        end_date = datetime.today()
        start_date = self.calculate_start_date(self.time_range_var.get(), end_date)
        data = stocks.fetch_stock_data(ticker, start_date, end_date.strftime('%Y-%m-%d'))
        macd_data = stocks.macd(data)
        self.draw_secondary_plot(f'{ticker} MACD', macd_data, 'MACD')

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