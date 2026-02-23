# Trading Pairs & Token Selection

## What is a Trading Pair?

A trading pair is two tokens you can swap between. Examples:
- **ASTRL/XRD** - Swap between Astrolescent and Radix
- **hUSDT/XRD** - Swap between Tether and Radix
- **hBTC/XRD** - Swap between Bitcoin and Radix

Every trade flips between the two tokens in your pair:
- Start with XRD → Buy ASTRL → Now hold ASTRL
- Later → Sell ASTRL → Back to holding XRD
- Repeat, making profit from price changes

---

## Price Impact Explained

**Default maximum: 5%**

Price impact = how much your trade moves the market price.

**Example:**
- xETH currently costs 1,500,000 XRD
- You want to buy 0.1 xETH (150,000 XRD worth)
- If pool is small, your buy pushes price to 1,525,000 XRD
- Price impact = 1.67% (you paid 1.67% more than market price)

**Radbot's 5% limit means:**
- Won't trade where your typical trade would cause >5% impact
- Protects you from terrible fills
- Ensures you get prices close to what you see

**Real Example:**

✅ **Good (Low Impact):**
- Pool has 2,000,000 XRD liquidity
- You trade 10,000 XRD (0.5% of pool)
- Price impact: ~0.5%
- You get almost exactly the market price

❌ **Bad (High Impact):**
- Pool has 100,000 XRD liquidity
- You trade 50,000 XRD (50% of pool!)
- Price impact: F#@k
- You would pay way over the market price
- Radbot wont execute trades for this pair until the impact improves.

---

## How to Choose a Trading Pair

### For Beginners

**Start with major tokens:**
1. **hUSDC/XRD** - Stablecoin, less volatile, easier to predict
2. **hETH/XRD** - Medium volatility, lots of liquidity
3. **hBTC/XRD** - Slightly more volatile, good volume

**Why these?**
- Everyone knows these tokens
- Tons of liquidity (your trades typically don't affect price)
- Predictable behavior
- Easy to understand news/fundamentals

### For Intermediate Traders

**Try non-XRD trade pairs:**
- ASTRL/CAVIAR - Astrolescent / CaviarNine
- DFP2/ASTRL - DefiPlaza / Astrolescent
- OCI/DFP2 - Ociswap / DefiPlaza
- Other DeFi tokens with solid volume

**Why?**
- More volatility = more profit opportunities
- Potentially Still liquid enough for safe trading
- Less crowded (fewer bots competing)

### For Advanced

**Smaller tokens** (be careful!):
- Must have sensible XRD weekly volume
- Watch for news/announcements
- Higher risk, higher potential reward
- Use smaller position sizes

### Avoid

❌ **Meme coins** - Too volatile, often manipulated
❌ **Brand new tokens** - No price history for indicators
❌ **Tokens with <50k volume** - You'll move the market
❌ **Tokens you've never heard of** - Research first!

---

## Checking Pair Health

**Before creating a trade, check:**

1. **7-Day Volume**
   - Should be stable or growing
   - If volume suddenly drops 50%, something's wrong
   - Check Ociswap to verify

2. **Price Chart**
   - Look at 7-day chart on Ociswap
   - Is it trending, ranging, or chaotic?
   - Match strategy to chart (Ping Pong for ranging, Manual/AI for trending)

3. **Pool Liquidity**
   - Check the pools on Ociswap
   - More liquidity = better
   - Aim for tokens with active, large pools, Radbot uses aggregated trade routes that will include those Ociswap pools

4. **Recent Trades**
   - Are trades happening regularly?
   - Or is it dead for days at a time?
   - Active pairs work better for trading bots

---

## Advanced Configuration

*These settings are in config files - only change if you know what you're doing.*

### Adjusting Volume Threshold

**File:** `config/advanced_config.json`

**Default:** 50,000 XRD

**When to increase (to 100,000+):**
- You're trading larger amounts (500+ XRD)
- You want only the most liquid tokens

**When to decrease (to 25,000+):**
- You want more token options
- You're trading tiny amounts (50 XRD)
- You understand the risks of lower liquidity

**Don't go below 10,000** - too risky.

### Adjusting Price Impact Limit

**Default:** 5%

**When to lower (to 2-3%):**
- You're trading large amounts
- You want the tightest spreads
- You're okay with fewer trades

**When to raise (to 7-10%):**
- You're willing to pay worse prices

**Don't go above 10%** - you'll lose so much to slippage.

---

## Troubleshooting

**"No trading pairs available"**

**Causes:**
1. You have not searched for and added any trade pairs yet

**Fixes:**
- Search for trade pairs in the Create Trade - "Configure Trade Pairs" page and add them to your Trading Pairs of Interest list. You then need to click the pair in that list to move it to the Radbot Trading Pairs list. Pairs in the Radbot Trading Pairs list build price history data and can be selected from the Create Trade page.

**"Trades executing at worse prices than expected"**

**Causes:**
1. Low liquidity pair
2. High volatility period
3. Your trade size is too large, split it into multiple trades.

**Fixes:**
- Use smaller trade amounts
- Trade during higher liquidity hours (US/EU daytime)
- Switch to more liquid pair
- Check pool sizes before trading

**"Price data seems wrong/stale"**

**Causes:**
1. Radbot's price cache needs refresh
2. Pool had recent liquidity change
3. Network sync issue

**Fixes:**
- Restart Radbot
- Wait for 10-minute price update cycle
- Verify prices on Astrolescent directly
- Check logs for API errors

---

## FAQ

**Q: Can I trade non-XRD pairs (like xETH/xUSDT)?**

A: Absolutely. Radbot enables you to add a vast selection of trade pairs. Most Radix network trading currently happens against XRD.

**Q: Why don't I see [specific token]?**

A: Either:
- Doesn't have a high enough price
- Too much price impact for typical trade sizes


**Q: What's the smallest amount I can trade?**

A: Technically as low as 1 XRD, but:
- Transaction fees (~0.5-1 XRD) eat into tiny trades
- Recommended minimum: 100 XRD per trade
- Ideal starting size: 500-1000 XRD

**Q: Do pairs ever disappear after I create a trade?**

A: No:
- To remove a pair from Radbot there needs to be no open trades of that pair.
- Then click the pair you wish to remove from the Radbot Trading Pairs list. This will stop Radbot accumulating price data for that pair.
- You may then delete the pair from Radbot by clciking the red X next to the pair in the Trading Pairs of Interest list.
- You may re-add trading pairs again any time, however pair price history will need to start from scratch.

**Q: Should I trade multiple pairs simultaneously?**

A: You can! Just make sure:
- You have enough tokens for each of them
- You're not over-complicating monitoring for yourself
- Each trade pair has proper liquidity
- Start with 1-2 pairs until comfortable
