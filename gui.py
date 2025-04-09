import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import stocks
import pandas as pd
import matplotlib.pyplot as plt

class StockAnalysisApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Stock Analysis")
        self.geometry("800x500")
        self.configure(bg="#f4f4f4")
        self.degree_var = tk.IntVar(value=3)
        self.dark_mode = tk.BooleanVar(value=False)

        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(frame, text="Stock Input")
        input_frame.grid(row=0, column=0, columnspan=4, pady=10, sticky="ew")

        ttk.Label(input_frame, text="Ticker:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticker_entry = ttk.Entry(input_frame, width=10)
        self.ticker_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ticker_entry.insert(0, 'AAPL')

        ttk.Label(input_frame, text="Start Date:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_date_entry = ttk.Entry(input_frame, width=12)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)
        self.start_date_entry.insert(0, '2024-01-01')

        ttk.Label(input_frame, text="End Date:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.end_date_entry = ttk.Entry(input_frame, width=12)
        self.end_date_entry.grid(row=2, column=1, padx=5, pady=5)
        self.end_date_entry.insert(0, string=datetime.today().strftime('%Y-%m-%d'))
        ttk.Button(input_frame, text="Today", command=self.set_current_date).grid(row=2, column=2, padx=5)


        button_frame = ttk.LabelFrame(frame, text="Actions")
        button_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky="ew")

        ttk.Button(button_frame, text="Show Graph", command=self.show).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="Bollinger", command=self.boll).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(button_frame, text="RSI", command=self.RSI).grid(row=0, column=2, padx=10, pady=10)
        ttk.Button(button_frame, text="MACD", command=self.MACD).grid(row=0, column=3, padx=10, pady=10)
        ttk.Button(button_frame, text="Predict Graph", command=self.predict_graph).grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="Predict", command=self.analyze_stock).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(button_frame, text="Export Result", command=self.export_results).grid(row=1, column=2, padx=10, pady=10)
        ttk.Button(button_frame, text="Show Headlines", command=self.display_headlines_sentiment).grid(row=1, column=3, padx=10, pady=10)
        ttk.Button(button_frame, text="Regression", command=self.show_regression).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="Polynomial Regression", command=self.show_polynomial_regression).grid(row=2, column=1, padx=10, pady=10)
        ttk.Label(button_frame, text="Degree:").grid(row=2, column=2, padx=5)
        self.degree_spinbox = ttk.Spinbox(button_frame, from_=1, to=10, textvariable=self.degree_var, width=5)
        self.degree_spinbox.grid(row=2, column=3, padx=5)

        self.last_result = None


    def set_current_date(self):
        today = datetime.today().strftime('%Y-%m-%d')
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, today)

    def analyze_stock(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        if isinstance(data['Close'], pd.DataFrame):
            data['Close'] = data['Close'].squeeze()
        analysis_result = stocks.predict_stock_movement(data, ticker)
        self.last_result = {
            'Ticker': ticker,
            'Start Date': start_date,
            'End Date': end_date,
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
        if headlines_sentiment:
            window = tk.Toplevel(self)
            window.title(f"{ticker} Headlines and Sentiment")
            text_widget = tk.Text(window, wrap=tk.WORD, width=100, height=25)
            text_widget.pack(padx=10, pady=10)
            for idx, (headline, sentiment) in enumerate(headlines_sentiment, 1):
                text_widget.insert(tk.END, f"{idx}. {headline} - Sentiment: {sentiment:.2f}\n")
        else:
            messagebox.showwarning("No Headlines", "No headlines found for this stock.")

    def show(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        stocks.showgraph(data)

    def boll(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        stocks.bollinger_bands(data)
        stocks.showboll(data, ticker)

    def RSI(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        stocks.rsi(data)
        stocks.showRSI(data, ticker)

    def MACD(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        stocks.macd(data)
        stocks.showMACD(data, ticker)

    def predict_graph(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        stocks.moving_averages(data)
        stocks.bollinger_bands(data)
        stocks.rsi(data)
        stocks.plot_projection(data, ticker)


    def show_regression(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        result = stocks.linear_regression_trend(data)

        plt.figure(figsize=(10, 6))
        plt.plot(result['Datetime'], result['Close'], label='Close Price')
        plt.plot(result['Datetime'], result['LR Trend'], label='Linear Regression', linestyle='--')
        plt.title(f'{ticker} Linear Regression Trend')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def show_polynomial_regression(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        degree = self.degree_var.get()
        data = stocks.fetch_stock_data(ticker, start_date, end_date)
        result = stocks.polynomial_regression_trend(data, degree=degree)

        plt.figure(figsize=(10, 6))
        plt.plot(result['Datetime'], result['Close'], label='Close Price')
        plt.plot(result['Datetime'], result['Poly Trend'], label=f'Polynomial Regression (deg={degree})', linestyle='--')
        plt.title(f'{ticker} Polynomial Regression Trend')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    app = StockAnalysisApp()
    app.mainloop()