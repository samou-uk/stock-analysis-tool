required_packages = [
    "yfinance",
    "matplotlib",
    "pandas",
    "ta",
    "requests",
    "beautifulsoup4",
    "textblob",
    "numpy",
    "mplfinance",
    "scikit-learn",
    "pandas-market-calendars",
    "pytz"
]

if __name__ == "__main__":
    import subprocess
    import sys

    for package in required_packages:
        try:
            __import__(package)
            print(f"{package} is already installed.")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
