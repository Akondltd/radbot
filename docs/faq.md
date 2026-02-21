# Frequently Asked Questions

## Getting Started

**Q: How much XRD do I need to start?**

A: Minimum ~100 XRD:
- 50-75 XRD for the trade itself
- 25-50 XRD for transaction fees and reserves

Recommended starting amount: 5000 XRD to have room for multiple trades and comfortable buffer.

**Q: Can I use Radbot on a phone/tablet?**

A: No, Radbot is desktop software only (Windows/Mac/Linux). It needs to run continuously to monitor trades, which mobile devices can't do reliably. You can use Remote Desktop to check it from mobile, though.

**Q: Do I need to leave my computer on 24/7?**

A: Yes, for Radbot to work. Radbot needs to:
- Check prices every 10 minutes
- Execute trades when conditions are met
- Monitor your positions continuously

Alternatives:
- Use an old laptop dedicated to trading
- Run it on a home server
- Use a cheap cloud VM (advanced users)

**Q: Is my money safe?**

A: Your funds are on the Radix ledger, not in Radbot. Radbot just has permission to trade with them (like giving your accountant access to your bank account). As long as your computer isn't compromised by malware, your funds are safe.

**Q: Can Radbot steal my tokens?**

A: No. Radbot is open-source local software. All trades go through official Radix APIs. Your private keys stay in your encrypted wallet file. If you're paranoid, check the source code yourself.

**NOTE**
Make sure that you downloaded Radbot via https://www.akond.co.uk/radbot
The only official Radbot source. Forked versions should be avoided as it may have been tampered with.

---

## Strategy Questions

**Q: Which strategy should I use as a beginner?**

A: Start with **Ping Pong**:
- Easiest to understand
- Predictable behavior
- Works well in sideways markets
- Set it and forget it

After 1-2 weeks, try Manual or AI Strategy.

**Q: Can I run multiple strategies at once?**

A: Yes! You can create separate trades:
- Trade 1: hETH/XRD with Ping Pong
- Trade 2: hUSDT/XRD with Manual
- Trade 3: hBTC/XRD with AI Strategy

Just make sure you have enough tokens for each to get started.

**Q: How long until I see profits?**

A: Depends on strategy and market:
- **Ping Pong:** Days to weeks (needs price to hit your levels)
- **Manual:** Days to weeks (needs indicator signals)
- **AI Strategy:** weeks (needs learning time)

Don't expect overnight riches. This is automated trading, not gambling.

**Q: What's a good win rate?**

A: For crypto bots:
- **50-55%:** Average (you're doing fine)
- **55-60%:** Good (better than most)
- **60-65%:** Excellent (you're in the top 20%)
- **65%+:** Exceptional (or you're in a lucky streak)

Remember: 60% win rate with 1:1 risk/reward = 20% profit over many trades.

**Q: Why does Manual strategy skip some signals?**

A: The ADX trend filter! If market is ranging (ADX < 25), Manual strategy holds to avoid whipsaw losses. This protects you from false signals in choppy markets. Check logs to see: "Market not trending, holding to avoid whipsaw."

**Q: I switched from AI Strategy to Manual/Ping Pong and my trade amount looks lower. What happened?**

A: AI Strategy uses **Kelly sizing** which only trades a portion of your position (10-100%) based on recent performance. The untapped portion is "reserved" in your wallet.

When you switch strategies, this reserved amount stays in your wallet temporarily. **It will automatically rejoin your trade** on the next execution when the trade flips back to that token.

**Example:**
- AI Strategy had 1.0 xETH
- Kelly sizing traded 0.4 xETH → 1200 XRD (reserved 0.6 xETH in wallet)
- You switch to Ping Pong
- Trade shows: 1200 XRD
- Your wallet also has: 0.6 xETH (reserved, not shown in trade)
- Next trade executes: Buys xETH → receives 0.45 xETH + **0.6 reserved = 1.05 xETH total**

**Your position isn't lost** - it's just split across the active trade and wallet temporarily. Check logs for "Kelly Recovery" messages to see when reserved amounts rejoin trades.

---

## Trade Execution

**Q: Why didn't my trade execute when signals said "execute"?**

A: Several reasons:
1. **Price moved** - By the time Radbot tried to trade, price changed
2. **Price impact too high** - Your trade would move market >5%
3. **Insufficient balance** - Not enough tokens
4. **Network issues** - Radix API temporarily unavailable
5. **Ping Pong thresholds** - Price not within your buy/sell range

Check logs for exact reason.

**Q: Trades are executing at worse prices than I see on Ociswap. Why?**

A: **Price impact** (slippage). When you trade, you move the market price slightly. Larger trades = more impact. Solutions:
- Trade smaller amounts
- Use more liquid pairs (higher volume)
- Trade during high-liquidity hours

**Q: How often does Radbot check prices?**

A: Every 10 minutes. This is deliberate:
- Prevents over-trading
- Reduces transaction fees
- Avoids noise in price data
- Focuses on meaningful moves

Radbot is not a day-trading bot. It's for swing trading over hours/days/weeks.

**Q: Can I force a trade manually?**

A: Not through Radbot GUI. Radbot follows strategy rules. If you want manual control, you'd need to:
1. Pause the trade
2. Trade manually on Ociswap
3. Update trade manually in Radbot

Not recommended - defeats the purpose of automation.

---

**Q: "Insufficient balance" but I have enough tokens**

**Causes:**
- Radbot sees stale balance data
- Recent transaction not yet confirmed
- Reserved amount from another trade

**Fix:**
- Wait 3 minutes for Radix network confirmation and balance refresh
- Restart Radbot

**Q: Wallet shows wrong balance**

**Fix:**
- Wait 3 minutes for Radix network sync and balance refresh
- Trade values are "reserved" to prevent you withdrawing funds that are required to trade

**Q: "Price impact exceeds limit" - what does this mean?**

A: Your trade would move the market price more than 5%, so Radbot rejected it to protect you from bad fills. Solutions:
- Reduce trade amount by 50%
- Switch to more liquid pair
- Wait for higher liquidity
- Check pool size on Ociswap

**Q: Radbot stopped executing trades, just says "hold"**

**Possible causes:**
1. **Manual strategy + ranging market** - ADX filter is protecting you
2. **AI strategy + low confidence** - Indicators aren't agreeing
3. **Ping Pong + price out of range** - Waiting for your price levels

**Check logs to see exact reason.**

---

## Profit & Loss

**Q: How is profit calculated?**

A: Compared to your starting token:
- Started with 100 XRD
- Now have 110 XRD equivalent
- Profit = 10 XRD (10%)

For non-compounding trades, profit accumulates in wallet separately.

**Q: I'm profitable but then gave it all back. What happened?**

A: Welcome to trading! This is normal. Solutions:
- Use **trailing stop** to lock in profits
- Use **compounding** so position grows
- Review if strategy still matches market conditions

**Q: AI Strategy is losing money. Should I stop it?**

A: Check:
1. **How long running?** Needs a few weeks to show true performance
2. **Win rate?** If < 30%, something's wrong
3. **Market conditions?** Extreme bull/bear markets confuse bots
4. **Kelly sizing working?** Should reduce position during losses

If losing after a month with 40%+ trades, review logs.

**Q: Transaction fees are eating my profits!**

A: Radix fees are low (~0.5-1 XRD per trade), but they add up:
- 10 trades = 5-10 XRD in fees
- You need >5-10 XRD profit to break even

Solutions:
- Trade larger amounts 
- Use Ping Pong (fewer trades)
- Avoid higher-frequency strategies

---

## Advanced Questions

**Q: Can I backtest strategies before running them?**

A: AI Strategy does this automatically every 7 days. For Manual/Ping Pong, no built-in backtesting. You'd need to:
- Export historical data from database
- Backtest in Excel/Python
- Advanced users only

**Q: Can I add custom indicators?**

A: Not through GUI. Would require:
- Python programming skills
- Modifying indicator files
- Understanding Radbot architecture

Most users won't need this - existing indicators cover 90% of strategies.

**Q: Does Radbot work with hardware wallets?**

A: No. Hardware wallets require manual confirmation for each transaction. Radbot needs to sign automatically. Use a software (hot) wallet and keep hardware (cold) wallet for long-term storage.

**Q: Can I run Radbot on multiple computers with same wallet?**

A: Don't! Two bots with same wallet will:
- Conflict with each other
- Execute duplicate trades
- Confuse balance tracking
- Potentially lose money

**Q: Where is my data stored?**

A:
- **Wallet file:** Wherever you saved it
- **Database:** `radbot.db` in Radbot/data folder
- **Logs:** `.log` file extension
- **Config:** `config/` subfolder

Backup the database and wallet file regularly!

**Q: Can I export my trade history?**

A: Yes:
1. **Database file:** Copy `radbot.db`, open with DB Browser for SQLite
2. **Trade History tab:** View in Radbot GUI
3. **Logs:** Read text files with `.log` file extension

For Excel analysis, export from DB Browser.

---

## Community & Support

**Q: Is there a Discord/Telegram for Radbot users?**

A: Check Radix community channels:
- Radix Discord: General crypto discussions
- Radix Telegram: Community support
- GitHub: Report bugs, request features

**Q: Can I hire someone to set this up for me?**

A: In short .. "Hell No!" .. Be VERY careful:
- Never give anyone your seed phrase
- Never let them access your computer remotely unsupervised
- They could steal your funds

If you need help, post specific questions in community channels. Many experienced users willing to help for free.

**Q: I found a bug! How do I report it?**

A:
1. Check logs for error messages
2. Note exactly what you were doing when bug occurred
3. Check GitHub issues to see if already reported
4. Create new GitHub issue with:
   - What you expected to happen
   - What actually happened
   - Log excerpts (remove private info!)
   - Steps to reproduce

**Q: Can I request new features?**

A: Yes! GitHub issues. Popular requests:
- More indicators (usually not needed)
- Mobile app (not feasible)

Best requests: Small improvements to existing features.

---

## Safety & Security

**Q: Someone DM'd me offering to "optimize" my Radbot settings. Legit?**

A: **SCAM!** No legitimate support will:
- DM you first
- Ask for your seed phrase
- Ask for remote access
- Ask for payment upfront
- Promise guaranteed profits

Block and report them.

**Q: Should I share my trade results online?**

A: Your choice, but:
- ✅ Share win rates, strategy types, general approach
- ❌ Don't share wallet addresses (privacy risk)
- ❌ Don't share exact positions (makes you a target)
- ❌ Don't brag about huge profits (attracts scammers)

**Q: My friend wants me to trade for them using their wallet. Should I?**

A: Bad idea:
- Legal implications (you're trading their money)
- If you lose, friendship is over
- If you profit, they might want more
- Tax complications

Instead: Teach them to use Radbot themselves.

**Q: Is it safe to update Radbot while trades are running?**

A: Generally yes:
1. Backup database first
2. Stop Radbot
3. Update software
4. Restart Radbot
5. Verify trades still active

Active trades survive updates (data is in database, not the app).

---

## Still Have Questions?

**Check these resources:**
1. **Help Tab:** You're here! Browse other sections
2. **Logs:** Shows exactly what Radbot is doing
3. **GitHub README:** Technical documentation
4. **Radix Community:** Discord/Telegram

**Before asking for help, have ready:**
- What you were trying to do
- What actually happened
- Relevant log excerpts
- Radbot version
- Operating system

**Pro tip:** 90% of questions are answered by reading the logs. Check there first!
