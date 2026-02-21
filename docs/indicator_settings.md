# Technical Indicators Explained

*This guide explains the indicators available in Manual Strategy. AI Strategy uses all of these automatically - you don't need to configure them individually.*

---

## RSI (Relative Strength Index)

### What It Measures

RSI tells you if a token is **oversold** (too cheap, time to buy) or **overbought** (too expensive, time to sell). It's like a "price pressure" meter ranging from 0-100.

Think of it like a stretched rubber band:
- When RSI hits 30 → Rubber band is stretched down (oversold) → ready to snap back up (buy)
- When RSI hits 70 → Rubber band is stretched up (overbought) → ready to snap back down (sell)

### How Radbot Uses It

- **RSI < 30** → BUY signal (token is oversold, price likely to bounce up)
- **RSI > 70** → SELL signal (token is overbought, price likely to drop)
- **RSI between 30-70** → HOLD signal (no strong signal either way)

### Parameters You Can Change

**Period (default: 14)**
- How many candles to analyze
- Smaller periods (7-9) = more sensitive, gives more signals (but more false signals)
- Larger periods (20-25) = less sensitive, fewer signals (but more reliable)

**Oversold Threshold (default: 20)**
- Lower = waits for more extreme conditions
- Try 30 if you want to buy more often, shallower dips
- Try 40 if you want really early entry points (not recommended)

**Overbought Threshold (default: 80)**
- Higher = waits for more extreme conditions
- Try 70 if you want to sell before peak euphoria
- Try 60 if you want really early exits (not recommended)

### Best Used When

✅ Token is ranging (bouncing between two prices)
✅ You want to catch reversals
✅ Pairing with MACD to confirm trends

❌ Strong trending markets (RSI stays "overbought" during rallies)
❌ Low volume tokens (RSI needs good price data)

---

## MACD (Moving Average Convergence Divergence)

### What It Measures

MACD tracks **momentum** and **trend direction**. It compares two moving averages (fast vs slow) to show if the trend is strengthening or weakening.

Think of it like two race cars:
- Fast car (12-period MA) reacts quickly to price changes
- Slow car (26-period MA) reacts slowly
- When fast car pulls ahead → momentum is building → BUY
- When fast car falls behind → momentum is dying → SELL

### How Radbot Uses It

- **MACD Line crosses above Signal Line** → BUY signal (bullish momentum building)
- **MACD Line crosses below Signal Line** → SELL signal (bearish momentum building)
- **Lines moving parallel** → HOLD signal (trend continuing, don't trade yet)

### Parameters You Can Change

**Fast Period (default: 15)**
- The short-term moving average
- Lower = more responsive to recent prices

**Slow Period (default: 30)**
- The long-term moving average
- Higher = smoother, less affected by short-term noise

**Signal Period (default: 10)**
- The trigger line that confirms trades
- Lower = earlier signals (but more false starts)
- Higher = delayed but more reliable signals

### Best Used When

✅ Token is trending (clear uptrends or downtrends)
✅ You want to ride momentum
✅ Combining with MA Cross for trend confirmation

❌ Ranging/choppy markets (gives false signals)
❌ Fast-moving tokens (lags behind price)

---

## MA Cross (Moving Average Crossover)

### What It Measures

MA Cross compares **short-term price average** vs **long-term price average** to identify trend changes. When the short-term average crosses the long-term, it signals a trend shift.

Think of it like a ship changing direction:
- Short MA (12-period) = the bow of the ship, turns first
- Long MA (26-period) = the stern, turns slowly
- When bow crosses above stern → ship turning upward → BUY
- When bow crosses below stern → ship turning downward → SELL

### How Radbot Uses It

- **Short MA crosses above Long MA** → BUY signal ("golden cross" - uptrend starting)
- **Short MA crosses below Long MA** → SELL signal ("death cross" - downtrend starting)
- **MAs parallel/not crossing** → HOLD signal (trend continues)

### Parameters You Can Change

**Short Period (default: 12)**
- Fast-moving average
- Use 5-7 for more signals (but more whipsaws, not recommended)
- Use 12-15 for fewer, stronger signals

**Long Period (default: 26)**
- Slow-moving average
- Try 30-50 for major trend changes only
- Try 15-20 for quicker response

**Popular Combinations:**
- 12/26 = Default (good balance)
- 9/21 = Faster signals
- 50/200 = Major trend changes only ("institutional" setting)

### Best Used When

✅ Trending markets (uptrends or downtrends)
✅ You want to catch the start of big moves
✅ Combining with RSI to avoid false breakouts

❌ Ranging markets (gives constant false signals)
❌ Very volatile tokens (too much whipsaw)

---

## Bollinger Bands (BB)

### What It Measures

Bollinger Bands show **price volatility** using three lines:
- Middle band = 20-period moving average
- Upper band = Middle + (2 × standard deviation)
- Lower band = Middle - (2 × standard deviation)

Think of it like a highway with lanes:
- Middle line = center lane (average price)
- Upper/Lower bands = guardrails
- When price hits upper guardrail → overbought, time to sell
- When price hits lower guardrail → oversold, time to buy
- Bands widen = high volatility (expect big moves)
- Bands narrow = low volatility ("squeeze" - breakout coming)

### How Radbot Uses It

- **Price touches lower band** → BUY signal (oversold condition)
- **Price touches upper band** → SELL signal (overbought condition)
- **Price in middle** → HOLD signal (no extreme condition)

### Parameters You Can Change

**Period (default: 20)**
- How many candles for the middle band average
- Smaller (10-15) = more sensitive, tighter bands
- Larger (30-40) = smoother, wider bands

**Standard Deviation Multiplier (default: 2.0)**
- How wide the bands are
- Lower (1.5) = tighter bands, more signals (but more false signals)
- Higher (2.5-3.0) = wider bands, only extreme touches count

**"Squeeze" Detection:**
- When bands get very narrow, a big move is coming
- Radbot doesn't trade the squeeze directly, but it's a good manual indicator

### Best Used When

✅ Ranging markets (price bouncing between bands)
✅ You want to catch reversals at extremes
✅ Tokens with predictable volatility patterns

❌ Strong trending markets (price "walks the band" - stays at upper/lower)
❌ After major news (bands don't capture sudden volatility spikes)

---

## Combining Indicators (Manual Strategy)

### Why Combine?

One indicator can give false signals. Multiple indicators voting together = more reliable trades.

### Good Combinations

**1. RSI + MACD (Momentum Confirmation)**
- RSI < 20 AND MACD crosses up → Strong BUY (oversold + momentum turning)
- RSI > 80 AND MACD crosses down → Strong SELL (overbought + momentum dying)

**2. MA Cross + RSI (Trend + Timing)**
- MA golden cross AND RSI rising from 20 → Enter uptrend early
- Avoids buying rallies that are already overbought

**3. Bollinger Bands + MACD (Volatility + Momentum)**
- Price at lower BB AND MACD positive → Oversold bounce with momentum
- Price at upper BB AND MACD negative → Overbought drop with momentum

**4. All Four (Maximum Confirmation)**
- Requires 2/4 indicators to agree (50%+ rule)
- Fewer trades, but much higher quality entries/exits

### What Radbot Does

With Manual Strategy:
1. Calculates ALL selected indicators frequently
2. Each votes: BUY, SELL, or HOLD
3. If ≥50% vote BUY → Executes BUY
4. If ≥50% vote SELL → Executes SELL
5. Otherwise → Holds position

**Example:**
- RSI: BUY (RSI = 18)
- MACD: HOLD (no crossover yet)
- MA Cross: BUY (golden cross)
- Bollinger: HOLD (price in middle)

**Result:** 2 out of 4 vote BUY (50%) → Radbot BUYS

---

## Tips for Manual Strategy

**Start Simple**
- Use 2 indicators first (RSI + MACD is a good combo)
- Watch how they behave for a few days
- Add more once you understand them

**Match Market Conditions**
- **Ranging market?** Use RSI + Bollinger Bands
- **Trending market?** Use MACD + MA Cross
- **Not sure?** Use all four and let voting decide

**Check the Logs**
- Radbot logs why it made each trade
- Example: "Trade 42: Executing BUY - RSI: BUY(18.5), MACD: BUY(crossover), MA: HOLD"
- Learn which indicators are accurate for your token

**Adjust Based on Results**
- If RSI gives lots of false signals with 30/70 → Increase threshold to 20/80
- If MA Cross is too slow → Shorten the periods
- Track which combo works best and stick with it

---

## AI Strategy vs Manual Strategy

**Manual Strategy:**
- You pick 1-4 indicators
- They use fixed settings
- Simple majority voting
- You adjust settings manually based on results

**AI Strategy:**
- Uses 8 indicators automatically
- Adjusts indicator weights based on market regime
- Uses confidence scoring (not just voting)
- Auto-optimizes settings every 7 days
- Kelly criterion position sizing

Both work great - Manual gives you control, AI gives you automation. Try both and see which fits your style!
