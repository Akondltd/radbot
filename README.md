# RadBot

**Radix Aggregated DEX Trading Bot**

RadBot is an automated trading bot for the [Radix DLT](https://www.radixdlt.com/) network. It monitors token prices 24/7 and executes trades across aggregated DEX liquidity based on your chosen strategy.

## Features

- **Multiple Strategies** — Manual indicator-based, Ping Pong, and AI-powered machine learning
- **Technical Indicators** — RSI, MACD, Bollinger Bands, Moving Average Crossover, ATR, and more
- **AI Optimization** — Machine learning auto-tunes strategy parameters after sufficient trade data
- **Non-Custodial** — Your keys never leave your machine; wallet password stays in RAM only
- **Real-Time Dashboard** — Live price charts, balance tracking, trade history, and profit analytics
- **Aggregated DEX Routing** — Finds the best swap route across Radix DEX pools

## Quick Start

### Install from PyPI

```bash
pip install radbot
```

### Or clone and install locally

```bash
git clone https://github.com/AkondLtd/radbot.git
cd radbot
pip install -e .
```

### Run

```bash
radbot
```

## Requirements

- Python 3.11 or later
- Windows, Linux, or macOS
- An active internet connection (for Radix Gateway API access)
- XRD tokens in your wallet for trading and network fees

### Linux Prerequisites

Some dependencies include C extensions that need compilation. Install the build tools first:

```bash
# Ubuntu / Debian
sudo apt install python3-dev build-essential

# Fedora / RHEL
sudo dnf install python3-devel gcc

# Arch
sudo pacman -S base-devel
```

### macOS Prerequisites

```bash
xcode-select --install
```

## First Steps

1. **Load your wallet** — Create a new wallet, import a seed phrase, or load an existing wallet file
2. **Configure trade pairs** — Browse available token pairs and select which ones to track
3. **Create a trade** — Pick a pair, choose a strategy, set your amount, and start trading
4. **Monitor** — Watch your trades execute on the Active Trades tab

See the full [Getting Started Guide](docs/getting_started.md) for detailed instructions.

## Strategies

| Strategy | Description |
|----------|-------------|
| **Ping Pong** | Buy at a fixed low price, sell at a fixed high price — simple and predictable |
| **Manual** | You configure technical indicators (RSI, MACD, etc.) and RadBot follows the signals |
| **AI Strategy** | Machine learning analyses your trade history and optimises indicator parameters automatically |

## Project Structure

```
radbot/
├── core/           # Radix blockchain interaction (wallet, transactions, network)
├── config/         # Application and database configuration
├── constants/      # Strategy type definitions
├── database/       # SQLite database managers (trades, balances, tokens, history)
├── gui/            # PySide6 Qt GUI (tabs, components, styling)
├── images/         # Icons and images
├── indicators/     # Technical indicator implementations
├── models/         # Data models
├── services/       # Background services (trade monitor, price history, AI)
├── security/       # Dependency verification
├── utils/          # Utility helpers
├── docs/           # User documentation
├── libs/           # Platform-specific libraries (Cairo DLLs for Windows)
├── main.py         # Application entry point
└── version.py      # Version metadata
```

## Security

- Wallet passwords are held in RAM only and erased on exit
- Private keys are never written to disk unencrypted
- Seed phrases are never stored by RadBot
- Fee configuration uses compiled native modules with integrity verification
- Dependency hashes are verified at startup

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE-agpl-3.0.txt).

## Links

- [RadixTalk Community](https://radixtalk.com/)
- [Radix DLT](https://www.radixdlt.com/)
