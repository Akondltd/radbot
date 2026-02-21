# Advanced Features

*These features give you more control and protection for your trades. Start with basics, then add these as you get comfortable.*

---

## Stop Loss Protection

### What It Does

Stop Loss automatically sells your position if you're losing too much money. Think of it as an emergency brake.

**Example:**
- You buy xETH at 1,500,000 XRD
- Set stop loss at 5%
- If xETH drops to 1,425,000 XRD (-5%) → Bot automatically sells
- You lose at least 5% instead of potentially 10%, 20%, or more

### When to Use It

✅ **Good for:**
- Volatile tokens (can crash fast)
- Overnight/weekend trading (you're not watching)
- Tokens you don't fully understand
- Protecting profits after a good run

❌ **Skip if:**
- Using Ping Pong (already has defined prices)
- Token barely moves (stop loss won't trigger)
- You're okay with unlimited downside risk

### How to Set It Up

1. Go to **Active Trades** tab
2. Click **Edit** on your trade
3. Scroll to **Advanced Settings**
4. Enable **Stop Loss**
5. Enter percentage (e.g., 5 for 5%)
6. Click **Save**

**Recommended values:**
- Conservative: 3-5% (tight stop, less pain)
- Moderate: 7-10% (room to breathe)
- Aggressive: 12-15% (only for high conviction)

### Important Notes

⚠️ **Stop loss only works when holding the "risky" token:**
- You accumulate XRD → stop loss protects when holding xETH
- You accumulate xETH → stop loss protects when holding XRD

Why? You're only at risk when holding the volatile token. When you hold your accumulation token, you're already safe.

⚠️ **Stop loss checks every 10 minutes:**
- Not real-time (this isn't a day-trading bot)
- If price crashes 20% in 5 minutes, you might lose more than your stop
- Radix is less volatile than other chains, so this usually works fine

---

## Trailing Stop (Lock in Profits)

### What It Does

Trailing stop follows the price up and locks in profits. As price rises, your sell point rises with it.

**Example:**
- Buy xETH at 1,500,000 XRD
- Set 10% trailing stop
- xETH rises to 2,000,000 XRD (+33%!)
- Trailing stop is now at 1,800,000 XRD (10% below peak)
- xETH drops to 1,800,000 → Bot sells
- You locked in 20% profit instead of riding it all the way back down

**vs. Regular Stop Loss:**
- Stop loss = fixed floor ("don't lose more than X%")
- Trailing stop = moving floor ("keep at least X% of gains")

### When to Use It

✅ **Good for:**
- Strong uptrends (let profits run, but protect them)
- After you're already up 10%+ (lock in some gains)
- Tokens that pump hard then crash
- When you can't monitor constantly

❌ **Skip if:**
- Token is ranging (stop will trigger on normal pullbacks)
- You're not yet profitable (need to be UP first)
- You want to hold through volatility

### How to Set It Up

1. **Active Trades** → **Edit** → **Advanced Settings**
2. Enable **Trailing Stop**
3. Enter percentage (e.g., 5 for 5%)
4. Click **Save**

**Recommended values:**
- Tight: 5-7% (lock profits quickly, but might exit too early)
- Normal: 10-12% (balanced)
- Loose: 15-20% (ride the wave, more risk of giving back gains)

### How It Works

**Scenario:**

You're trading xETH/XRD, accumulating XRD, with 10% trailing stop:

1. Buy xETH at 1,500,000 XRD
2. Price rises to 1,600,000 → Trailing stop set at 1,440,000 (10% below)
3. Price rises to 1,800,000 → Trailing stop now at 1,620,000
4. Price rises to 2,000,000 → Trailing stop now at 1,800,000
5. Price drops to 1,900,000 → No action (above stop)
6. Price drops to 1,800,000 → BOT SELLS! (hit trailing stop)

**Result:** Entered at 1,500,000, exited at 1,800,000 = 20% profit locked in!

### Important Note

Trailing stops are a best effort and are unlikely to execute exactly at the price you would like, but below that price. It is dependent on market movements how far below.


---

## Compounding vs Non-Compounding

### Non-Compounding (Default)

**How it works:**
- Start with 100 XRD
- Radbot always trades 100 XRD
- Profits stay in your wallet (not reinvested)
- Position size never grows

**Example:**
- Trade 1: 100 XRD → 105 XRD (5% profit)
- Your wallet: 105 XRD
- Trade 2: Bot uses 100 XRD, leaves 5 XRD in wallet
- Trade 3: Still uses 100 XRD

**Profits accumulate in wallet, safe from trading losses.**

**Good for:**
- Beginners (simpler to track)
- Regularly withdrawing profits
- Conservative risk management
- Testing strategies

### Compounding

**How it works:**
- Start with 100 XRD
- After first profitable trade → 105 XRD
- Radbot now trades with 105 XRD
- After second profitable trade → 110 XRD
- Radbot now trades with 110 XRD
- Position grows exponentially

**Example:**
- Month 1: 100 XRD → 110 XRD (+10%)
- Month 2: 110 XRD → 121 XRD (+10%)
- Month 3: 121 XRD → 133 XRD (+10%)

With compounding: **+33% total**  
Without compounding: **+30% total** (10% three times on 100 XRD)

**Good for:**
- Long-term growth
- When you won't withdraw for months
- Confident in strategy
- Aggressive growth goals

**Risk:** Losing trades also compound. If strategy goes bad, you lose more.

### How to Enable Compounding

**When creating trade:**
1. **Create Trade** tab
2. Toggle **Compound Profit** to Yes
3. Create trade

**When Editing Trade**
1. **Active Trades** tab, click Edit button for the trade.
2. Check the **Compound Profit** check box
3. Edit Trade

---

## AI Strategy Optimization

### What Happens Automatically

If you're using AI Strategy, Radbot runs weekly optimization:

**Every 7 days:**
1. Radbot looks at last 90 days of price data
2. Tests 27 different parameter combinations
3. Finds which settings would have worked best
4. Auto-updates your trade with those settings
5. Saves results to database

**What gets optimized:**
- Execution threshold (how strong signal needs to be)
- Confidence threshold (how confident indicators must be)
- Indicator weights (which indicators to trust more)

**You don't do anything - it's automatic.**

### Checking Optimization Results

**In logs:**
Look for:
```
AI Optimization for Trade 42 complete:
- Win rate: 58.3%
- Total return: +12.4%
- Sharpe ratio: 1.8
- Max drawdown: -8.2%
```

**What the numbers mean:**
- **Win rate:** % of trades that were profitable
- **Total return:** How much you would have made
- **Sharpe ratio:** Return vs risk (higher = better, >1 is good)
- **Max drawdown:** Biggest loss from peak (lower = better)

### Kelly Criterion Position Sizing

**After 10 trades**, AI Strategy starts using Kelly criterion:

**What it does:**
- Calculates your win rate and average win/loss size
- Adjusts position size based on recent performance
- Winning? Increase position (up to 80%)
- Losing? Decrease position (down to 10%)

**Example:**
- Trades 1-10: Uses 100% of position (learning)
- Trade 11: Win rate 60%, good R/R ratio → Kelly says use 65%
- Trade 15: Win rate dropped to 45% → Kelly says use 30%
- Trade 20: Back to 55% wins → Kelly says use 50%

**You see this in logs:**
```
Trade 42 Kelly Calculation:
  Win Rate: 60.0%
  Avg Win: +2.8% | Avg Loss: -1.5%
  R/R Ratio: 1.87
  Final Position Size: 65%
```

**Benefit:** Protects you during losing streaks automatically.

---

## Accumulation Token Strategy

### What It Means

Every trade has a goal: end up with more of ONE specific token.

**Example 1: Accumulate XRD**
- Your goal: Stack more XRD
- Radbot sells tokens when they rise (converts to XRD)
- Radbot buys tokens when they fall (spend XRD to buy cheap)
- Over time: XRD balance grows

**Example 2: Accumulate xETH**
- Your goal: Stack more xETH
- Radbot sells xETH when it rises (to XRD)
- Radbot buys xETH back when it falls (cheaper)
- Over time: xETH balance grows

### Why It Matters

Strategies consider your goal:
- **Ping Pong:** Buys at low price, sells at high price (gains accumulation token)
- **Manual/AI:** Only takes trades that favor your accumulation token

**Set when creating trade** - can also be changed by editing the trade from the **Active Trades** tab

---

## Price Impact Protection

**Radbot automatically rejects trades with >5% price impact.**

What this means:
- Before each trade, Radbot simulates it
- If your trade would move market price >5%, Radbot cancels the process
- Protects you from terrible fills

**You see this in logs:**
```
Trade 42: Price impact 7.2% exceeds limit (5.0%)
Trade rejected to protect capital
```

**What to do:**
- Trade smaller amounts
- Wait for higher liquidity
- Switch to more liquid pair

---

## Database & History Tracking

### What Gets Saved

**Every trade execution:**
- Entry/exit prices
- Amounts traded
- Profit/loss
- Transaction IDs
- Timestamp

**Every few minutes:**
- Token prices
- Indicator values (if Manual strategy)
- Signal decisions

**Weekly (AI Strategy):**
- Optimization results
- Backtest performance
- Parameter changes

### Where to Find It

**Trade History tab:**
- All executed trades
- Profits/losses

**Database file:**
- `radbot.db` in installation folder /data
- SQLite format (can open with DB Browser)
- Contains everything for analysis

**.log files:**
- Text files with detailed operations
- Useful for debugging
- Check when something seems wrong

---

## Tips for Advanced Users

1. **Combine stop loss + trailing stop:**
   - Set 10% stop loss (hard floor)
   - Set 8% trailing stop (profit protection)
   - You're protected both ways

2. **Start trades small, compound later:**
   - First week: 50 XRD, non-compounding
   - Verify it works
   - Week 2: 500 XRD, enable compounding

3. **Use different strategies per pair:**
   - xUSDT/XRD: Ping Pong (stable)
   - xETH/XRD: Manual with RSI+MACD
   - xBTC/XRD: AI Strategy
   - See which performs best

4. **Check optimization logs weekly:**
   - See if AI is improving
   - If win rate dropping, might need to pause
   - If Sharpe ratio >2, you're crushing it

5. **Export database regularly:**
   - Backup your trade history
   - Analyze in Excel/Python
   - Track long-term performance

6. **Monitor reserved amounts (AI Strategy):**
   - Kelly sizing reserves portions of position
   - Check wallet to see reserved tokens
   - They'll get added back when flipping to that token

---

## FAQ

**Q: Can I change stop loss while trade is running?**

A: Yes! Edit trade anytime. New stop takes effect on next price check.

**Q: What if stop loss triggers while I'm asleep?**

A: Trade executes automatically. You'll see it in Trade History when you wake up. That's the point - protection even when you're not watching.

**Q: Does compounding work with stop loss?**

A: Yes. If stop triggers, you lose some position. If compounding is on, next trade uses the reduced amount.

**Q: Can I see what parameters AI chose?**

A: Check logs. Search for "AI Optimization" or "Parameters updated".

**Q: Will AI Strategy work for brand new tokens?**

A: Not well. Needs 90+ days of price history for best optimization. Stick to established tokens.

**Q: Can I turn off Kelly sizing for AI Strategy?**

A: Not currently. It's built into AI Strategy. Use Manual if you want full-position trading with indicators.
