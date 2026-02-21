# Trading Strategies

Radbot offers three trading strategies, each designed for different skill levels and trading styles.

---

## Strategy 1: Ping Pong (Best for Beginners)

### What It Does

Ping Pong is the simplest strategy - you set two fixed prices, and Radbot bounces between them:
- **Buy Price**: When the token drops to this price, buy it
- **Sell Price**: When the token rises to this price, sell it

Every time it "pings" and "pongs" between these prices, you make profit from the difference.

### Example

xETH is trading around 1,500,000 XRD:
- You set **Buy Price = 1,400,000** (buy when cheap)
- You set **Sell Price = 1,600,000** (sell when expensive)
- Radbot starts with XRD, waits for xETH to drop to 1,400,000, buys it
- Radbot now holds xETH, waits for price to rise to 1,600,000, sells it
- You just made profit from the 200,000 XRD price difference!

### When to Use It

✅ **Good for:**
- Tokens that bounce in a predictable range ("ranging markets")
- When you have a good sense of support/resistance levels
- Beginners learning how the bot works
- Stable, sideways markets

❌ **Bad for:**
- Strong trending markets (price runs away from your range)
- Very illiquid tokens (can't get the depth of liquidity you want)

### Pro Tips

1. **Set realistic ranges**: Check the token's 7-day price chart. Don't set a buy price that hasn't been hit in months.
2. **Start tight**: Better to have a 5% range and get some trades than a wide 15-20% range that never triggers.
3. **Watch liquidity**: Make sure the token has decent volume or your trades might impact the price.
4. **Be patient**: Ping Pong works best over days/weeks, not minutes.

---

## Strategy 2: Manual (For Traders)

### What It Does

You select technical indicators (RSI, MACD, MA, Bollinger Bands) and Radbot trades when they signal. Radbot needs at least 50% of indicators to agree before trading.

### Available Indicators

**RSI (Relative Strength Index)**
- Shows if a token is "oversold" (cheap, time to buy) or "overbought" (expensive, time to sell)
- When RSI < 20 → Buy signal
- When RSI > 80 → Sell signal
- Best for: Catching bounces in ranging markets

**MACD (Moving Average Convergence Divergence)**
- Follows momentum and trends
- When MACD line crosses above signal → Buy
- When MACD line crosses below signal → Sell
- Best for: Riding trends up or down

**MA Cross (Moving Average Crossover)**
- Compares short-term vs long-term average prices
- When short MA crosses above long MA → Buy (uptrend starting)
- When short MA crosses below long MA → Sell (downtrend starting)
- Best for: Catching major trend changes

**Bollinger Bands**
- Shows price volatility using bands
- Price touches lower band → Buy (oversold)
- Price touches upper band → Sell (overbought)
- Best for: Volatility-based trading

### How It Works

1. You pick 1-4 indicators
2. Radbot calculates all of them frequently
3. Each indicator "votes" BUY, SELL, or HOLD
4. If ≥50% vote the same way → Radbot executes that trade
5. Otherwise → Radbot holds and waits

### ADX Trend Filter (Auto-Protects You)

Manual strategy includes ADX (Average Directional Index) which measures trend strength:
- **ADX < 25**: Market is choppy/ranging → Radbot holds (avoids whipsaw losses)
- **ADX ≥ 25**: Market is trending → Radbot follows indicator signals

This prevents Radbot from trading when indicators give false signals in messy markets.

### When to Use It

✅ **Good for:**
- Traders who understand technical analysis
- When you want more control than Ping Pong
- Testing which indicators work best for different tokens
- Learning what indicators mean through real trading

❌ **Bad for:**
- Complete beginners (start with Ping Pong first)
- Tokens with very low volume (indicators need good data)

### Pro Tips

1. **Start with 2 indicators**: Try RSI + MACD. More isn't always better.
2. **Match indicators to market**: Use RSI/BB for ranging, MACD/MA Cross for trending.
3. **Watch the logs**: Check why trades were executed to learn indicator behavior.
4. **Give it time**: Indicators need several days of data to start to work properly.

---

## Strategy 3: AI Strategy (Advanced)

### What It Does

The AI Strategy uses 8 different indicators simultaneously and **learns from results**. It's like Manual Strategy on steroids:
- Automatically adjusts indicator weights based on performance
- Adapts to market regimes (trending vs ranging vs volatile)
- Uses Kelly criterion to adjust position size to protect your capital
- Runs backtest driven optimization to find best parameters

### The 8 Indicators

AI Strategy combines:
1. **RSI** - Overbought/oversold detection
2. **MACD** - Trend following
3. **Bollinger Bands** - Volatility
4. **MA Cross** - Trend changes
5. **Stochastic RSI** - Enhanced momentum
6. **ROC (Rate of Change)** - Momentum strength
7. **Ichimoku Cloud** - Support/resistance
8. **ATR** - Market volatility

### Adaptive Features

**1. Market Regime Detection**

The AI Strategy auto-detects market conditions:
- **Trending Up/Down**: Increases weight on MACD, MA Cross (trend followers)
- **Ranging**: Increases weight on RSI, Bollinger Bands (mean reversion)
- **High Volatility**: Increases weight on Bollinger Bands, ATR

Weights adjust **per trade** based on current 50-candle window.

**2. Kelly Criterion Position Sizing**

After 10 trades, the AI Strategy starts adjusting position size:
- **Winning streak?** → Increases position up to 80%
- **Losing streak?** → Reduces position down to 10%
- **Formula**: Kelly % = (Win Rate × Reward/Risk - Loss Rate) / Reward/Risk

This protects your capital during drawdowns and capitalizes on hot streaks.

**3. Weekly Optimization**

Every 7 days, the AI Strategy:
1. Backtests 27 different parameter combinations on past 90 days of data
2. Finds the settings with best win rate + return + Sharpe ratio
3. Auto-updates Radbot's parameters
4. Saves results to database for tracking

This means the AI Startegy continuously improves based on what actually works.

### When to Use It

✅ **Good for:**
- Users who want "set it and forget it" trading
- Demonstrating AI capabilities vs human traders
- Tokens with consistent volume and data
- Long-term trading (months to years)

❌ **Bad for:**
- Brand new tokens (need historical data)
- Extreme bull/bear markets (optimization lags market shifts)
- Tokens with low daily volume

### How to Use It

1. Create trade, select "AI Strategy"
2. Enter starting amount
3. **First 10 trades**: AI Strategy uses 100% position (learning phase)
4. **After 10 trades**: Kelly sizing activates
5. **After 7 days**: First optimization runs
6. Check **Trade History** to see learning progress

### Pro Tips

1. **Give it time**: AI Strategy needs weeks to show its strength
2. **Larger amounts**: AI Strategy works better with $100+ XRD worth (stronger data per trade)
3. **Compare to Manual**: Run same token on Manual + AI to see difference

---

## Choosing Your Strategy

**Start with Ping Pong if:**
- This is your first automated trading bot
- You want predictable, understandable behavior
- The token is ranging in a clear channel

**Use Manual if:**
- You understand technical indicators
- You want control over which signals to follow
- You're learning technical analysis

**Use AI Strategy if:**
- You want maximum automation
- You're comfortable with the AI Strategy learning from losses
- You want to compete with professional traders
- You're in it for the long haul (months/years)

**Can I run multiple strategies on the same token?**

Yes! You can create separate trades:
- Trade 1: xETH/XRD with Ping Pong
- Trade 2: xETH/XRD with AI Strategy

This lets you compare which works better. Just make sure you have enough tokens for both trades.

---

## Advanced Strategy Settings

All strategies support:

**Compounding vs Non-Compounding**
- **Non-Compounding**: Profits stay in wallet, always trades the starting amount when possible, and will recover to it after a loss with future profits
- **Compounding**: Profits get reinvested, position grows over time

**Accumulation Token**
- Pick which token you want to end up with more of
- Radbot will prefer trades that increase this token
- Example: Accumulate XRD → Radbot sells tokens when they rise, buys when they fall

**Stop Loss & Trailing Stop**
- **Stop Loss**: Auto-sells if you lose X% (protects against crashes)
- **Trailing Stop**: Locks in profits by selling if price drops X% from peak
- Can be set at trade creation or found in Active Trades → Edit

**CAUTION**: Stop losses and Trailing Stops are a best effort defence, however they cannot protect you in extremely volatile markets as the price they sell at is not guaranteed. Use with caution.

See **Advanced Features** documentation for details on these settings.
