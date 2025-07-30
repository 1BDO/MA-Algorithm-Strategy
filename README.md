## MA Algorithm Strategy

This project implements an automated trading bot designed to execute a Mean Reversion strategy on cryptocurrency markets, specifically interacting with the Delta Exchange API. It leverages technical indicators like Moving Averages (MA) and Average True Range (ATR) to identify trading opportunities and manage risk.

### Overview

The MA-Algorithm-Strategy bot automates the process of analyzing market data, identifying trends, and placing trades based on predefined technical indicators and risk management principles. It's built to operate on the Delta Exchange, ensuring secure and authenticated API interactions for fetching data, managing positions, and executing orders. The strategy employs the Kelly Criterion for optimal position sizing and includes features like trailing stop-loss and a portfolio-wide stop-loss to protect capital.

### Features

*   **Automated Trading:** Continuously monitors market conditions and executes trades without manual intervention.
*   **Mean Reversion Strategy:** Implements a strategy based on 50-period and 200-period Moving Averages to identify overbought/oversold conditions within a trend.
*   **Dynamic Position Sizing:** Utilizes the Kelly Criterion to calculate optimal trade sizes based on win probability, risk-reward ratio, and bankroll, with adjustments for initial margin requirements.
*   **Risk Management:** Includes trailing stop-loss for open positions and a comprehensive portfolio stop-loss to prevent significant capital drawdowns.
*   **Delta Exchange API Integration:** Securely interacts with the Delta Exchange using Signeture authentication for all REST API calls.
*   **Historical Data Processing:** Fetches and processes historical OHLCV data using the CCXT library for indicator calculations.
*   **Robust Logging:** Provides detailed logging for all operations, making it easy to monitor performance and debug issues.

### Prerequisites

Before running the bot, ensure you have the following installed:

*   Python 3.8+
*   `pip` (Python package installer)

### Tech Stack

*   **Languages:** Python
*   **Libraries:** `pandas`, `numpy`, `ccxt`, `requests`, `python-dotenv`, `schedule`, `certifi`, `hmac`, `hashlib`, `json`, `logging`, `datetime`, `urllib.parse`

### Setup or Installation Steps

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/MA-Algorithm-Strategy.git
    cd MA-Algorithm-Strategy
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    (Note: A `requirements.txt` file is not explicitly provided in the project structure, but it's a standard practice. You might need to create one manually based on the `import` statements in the code.)

    To create `requirements.txt`:
    ```bash
    pip freeze > requirements.txt
    ```

5.  **Configure API Credentials and Parameters:**

    Create a `.env` file in the root directory of the project and add your Delta Exchange API key and secret, along with other trading parameters.

    ```dotenv
    DELTA_API_KEY=YOUR_DELTA_API_KEY
    DELTA_API_SECRET=YOUR_DELTA_API_SECRET
    DELTA_BASE_URL=https://cdn-ind.testnet.deltaex.org # Or production URL
    BANKROLL=1000 # Your initial bankroll for calculations
    ```

    **Important:** Replace `YOUR_DELTA_API_KEY` and `YOUR_DELTA_API_SECRET` with your actual API credentials obtained from Delta Exchange.

### Usage Example

To start the trading bot, simply run the `main.py` script:

```bash
python main.py
```
