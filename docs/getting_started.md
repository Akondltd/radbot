# Getting Started with Radbot

## What is Radbot?

Radbot is an automated aggregated DEX trading bot for the Radix DLT network. It monitors token prices 24/7 and executes trades based on your chosen strategy. Think of it as a robot trader that never sleeps, never gets emotional, and follows your rules precisely.

## Quick Start (5 Minutes)

### Step 1: Load Your Wallet

1. Click the **Wallet** tab
2. Choose one of three options:
   - **Load Existing**: Select your wallet file (.json) and enter password
   - **Create New**: Generate a brand new wallet with a 24-word seed phrase
   - **Import**: Enter an existing 24-word seed phrase
3. The rest of Radbots tabs will then become available.

**IMPORTANT:** Your password stays in RAM (temporary memory) so Radbot can sign trades. Radbot needs it to function. When you close Radbot, the password is erased from RAM. To unload your wallet simply remove the password from the Wallet Password field in the Wallet tab.

**CRITICAL:** Write down your 24-word seed phrase on paper and store it somewhere safe. If you lose this, you lose access to your funds forever. No one can recover it. Radbot does not store this data, it is never written to disk.

### Step 2: Check Your Balance

Once your wallet loads, you'll see:
- **XRD balance**: The main Radix token
- **Other tokens**: Any tokens you currently hold

You ideally need at least ~1000 XRD to start trading (900 XRD for the trade + 100 XRD for network fees from trading), maybe even 5500 XRD if the price is way down.

### Step 3: Create Your First Trade

## Configure Trade Pairs

1. Go to the **Create Trade** tab, on first visit the *Configure Trade Pairs* button will be flashing, click it.
2. Find and add the pairs you may like to trade with the search tool.
3. Click all of the pairs you wish to start trading in the immediate future, that you have added to the *Trading Pairs of Interest*. They will be added to the *Radbot Trading Pairs* list so they can start to accumulate price history data.
4. Click the *Back to Create Trade* button to return to the trade creation page.

**NOTE** Impact is very important. It gives a guide on how much the market will move if a $500 value trade is made on that pair. Around 2% is about as low as we typically see. The higer the impact the less likely the chance of profitable trades.

## Create Trade

1. Pick a trading pair (like hETH/hUSDC or hUSDT/XRD) from the list of pairs that are now available to you. It will populate the rest of the create page with data such as token prices.
2. Select the token you wish to start the trade with, you mist have some of this token in your wallet.
3. Select the token you wish to accumulate.
4. Set the amount of the start token you wish to place in the trade.
5. Choose a strategy:
   - **Manual**: You pick indicators (RSI, MACD, etc.) and Radbot follows them
   - **Ping Pong**: Buy low at a fixed price, sell high at a fixed price - simple!
   - **AI Strategy**: Let the AI Strategys machine learning figure out the best settings automatically
6. Enter starting amount (start small while learning - maybe try 500 XRD worth)
7. Click **Create Trade**

### Step 4: Monitor Your Trade

Switch to the **Active Trades** tab to watch your bot work:
- **Current Position**: What token you're holding right now
- **Strategy Used**: What strategy the trade is using
- **Total Profit**: Whether you're winning or losing
- **Current Status**: Is the trade active or is it paused
- **Action Buttons**: Each trade can be edited to fine tune the settings. There is also extented information for each trade, a method to pause/unpause trades and a button to delete the trade.

The bot checks prices frequently and trades when conditions are right.

## Your First Strategy: Start Simple

**We recommend starting with Ping Pong for your first trade:**

Why? It's the easiest to understand:
1. You set a "buy price" (buy when the token is cheap).
2. You set a "sell price" (sell when the token is expensive).
3. The bot flips between them, with you pocketing the difference.

Example:
- xETH currently costs 1,500,000 XRD
- Set buy price to 1,400,000 (buy when it drops)
- Set sell price to 1,600,000 (sell when it rises)
- Every flip makes you profit from the 200,000 XRD difference

## Safety First

✅ **DO:**
- Start with small amounts (~5000 XRD)
- Test for a few days before adding more funds
- Check your trades daily until you're comfortable
- Keep your seed phrase written down and safe

❌ **DON'T:**
- Put your entire wallet into one trade
- Trade more than you can afford to lose
- Share your password or seed phrase with anyone ... EVER!!!
- Panic-close trades after one loss (give Radbot time to work, the machine learning needs 10 trades to have data to start working with on each trade)

## What Happens Next?

Once your trade is active:
1. **Trade Monitor** checks prices frequently and builds price data
2. When strategy signals "execute", Radbot trades automatically
3. You see updates in the Active Trades tab
4. Profits from non-compounding trades stay in your wallet
5. Radbot keeps going until you pause or delete the trade
6. Think of each trade as an infinite loop.

## Need Help?

- **Help Tab**: You're here! Browse other sections for specific topics
- **Logs**: Check files with a .log file extension if something seems wrong
- **Discord**: Join the Radix community

## Next Steps

Once you're comfortable with basic trading:
1. Read **Trading Strategies** to understand Manual and AI strategies
2. Check **Indicator Settings** to learn what RSI, MACD, etc. mean
3. Explore **Advanced Features** for stops, compounding, and AI optimization

Remember: Trading involves risk. Never trade with money you can't afford to lose. Radbot is a tool that helps you trade, but it can't predict the future or guarantee profits.
