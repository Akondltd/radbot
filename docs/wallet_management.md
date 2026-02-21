# Wallet Management

## Understanding Your Wallet

Your Radix wallet is like a digital bank account. It holds:
- **XRD** - The main Radix token (like dollars)
- **Other tokens** - ASTRL, hETH, hUSDC, hBTC, etc. (like stocks)

Your wallet has two important pieces:
1. **Address** - Like your bank account number (safe to share)
2. **Private keys** - Like your PIN code (NEVER share!)

Radbot needs access to your wallet to trade automatically. This guide explains how to manage that access safely.

---

## Three Ways to Set Up Your Wallet

### Option 1: Load Existing Wallet (Most Common)

If you already have a Radix Wallet that you have created with Radbot:

1. Click **Wallet** tab
2. Click **Browse** select your wallet file (`.json` extension)
3. Enter your wallet password
4. Click **Load Wallet**
5. Your address and balances appear

Your wallet file is usually in:
- **Windows**: `Radbot Directory Path`
- **Mac**: `~/Radbot Directory Path`
- **Linux**: `Radbot Directory Path`

### Option 2: Create New Wallet

To generate a brand new wallet:

1. Click **Wallet** tab
2. Enter a strong password (12+ characters, mix of letters/numbers/symbols)
3. Click **Create Wallet**
4. Choose where to save the wallet file, default should be your Radbot directory.
5. **CRITICAL STEP**: A 24-word seed phrase appears - WRITE IT DOWN ON PAPER. Check you have the words written correctly. Then check them again. Please do not rush this process.
6. Store that paper somewhere safe (fireproof safe, safety deposit box, etc.) Consider also writing a copy of your seed phrase and hiding it in a second location. Never take a picture of your seed phrase, always write it.

**Why the seed phrase matters:**
- If you lose your wallet file → seed phrase can restore it
- If you forget your password → seed phrase can restore it
- If your computer crashes → seed phrase can restore it
- **If you lose the seed phrase → your funds are GONE FOREVER**

Nobody can recover a lost seed phrase. Not Radix, not Radbot, not anyone. It's mathematically impossible.

### Option 3: Import from Seed Phrase

If you have a seed phrase from another wallet, like the Radix Mobile Wallet:

1. Click **Wallet** tab
2. Enter a strong password (12+ characters, mix of letters/numbers/symbols)
3. Click **Import Wallet**
4. Enter your 24 words (in exact order, lowercase, space separated)
5. If you have only one wallet on that seed phrase click **Import Directly**, if it has more than 1 funded wallet to choose from the seed phrase, click **Scan for Mobile Wallets** The Radix Moble Wallet is HD capable so it is possible to have more than one wallet from one seed phrase
6. Choose where to save the new wallet file


---

## Security: How Radbot Handles Your Password

### The Problem

To trade automatically, Radbot needs to sign transactions. Signing requires your password. But storing passwords on disk is dangerous (hackers, malware, etc.).

### The Solution

Radbot uses **RAM-only password storage**:

**When you load a wallet:**
1. You enter your password once
2. Radbot keeps it in RAM (temporary computer memory)
3. Radbot uses it to sign trades automatically
4. Password stays there as long as Radbot is running

**When you close RadBot:**
1. RAM is cleared
2. Password disappears completely
3. Next time you open Radbot, you'll need to enter it again

This means:
- ✅ Bot can trade 24/7 without asking for password repeatedly
- ✅ Password never touches your hard drive (safe from most attacks)
- ✅ Closing Radbot = instant password wipe
- ❌ You need to re-enter password after computer restart

### What's in the Password Field?

You'll notice the password field stays filled while Radbot is running:
- This is **intentional** - it's there so Radbot can sign trades
- Don't delete it unless you want to unload your wallet
- It's only visible to you, obfuscated, on your local computer

**To unload your wallet:** Just delete the password from the field → wallet unloads.

**NOTE**
There are 2 Wallet Password fields on the Wallet page. One for loading, creating, importing, exporting your wallet and trading. The second is for withdrawing funds from the wallet. To withdraw funds your wallet password must be entered for a second time.

---

## Wallet Security Best Practices

### Critical Rules (DO NOT SKIP)

1. **Write down seed phrase on paper**
   - NOT on your computer (can be hacked)
   - NOT in cloud storage (can be compromised)
   - NOT in a photo (phones get lost)
   - Paper stored in a safe physical location

2. **Never share your seed phrase**
   - Not with support
   - Not with friends
   - Not with "Radix staff" (they'll never ask)
   - Not with "Radbot staff" (we will never ask)
   - Scammers will pretend to be support - ignore them

3. **Use a strong wallet password**
   - At least 12 characters
   - Mix uppercase, lowercase, numbers, symbols
   - Not your birthday, name, or common words
   - Unique password (not reused from other sites)

4. **Keep wallet file backed up**
   - Copy `wallet name.json` file to USB drive
   - Store USB in safe place
   - Or use seed phrase backup (more secure)

### Recommended (But Optional)

5. **Use a dedicated trading wallet**
   - Keep most funds in a separate "cold" wallet
   - Only put trading funds in RadBot wallet
   - Example: 10,000 XRD in cold wallet, 1,000 XRD in trading wallet

6. **Test with small amounts first**
   - Load wallet with just 500 XRD
   - Run Radbot for a week
   - Once comfortable, maybe add more funds

7. **Run Radbot on a clean computer**
   - Updated Windows/Mac with antivirus
   - No sketchy downloaded software
   - Don't visit risky websites while trading

8. **Verify your address after loading**
   - Click the address to copy it
   - Paste into Radix Dashboard to verify it's yours
   - Check the first/last 8 characters match

---

## Wallet Features in Radbot

### Balance Display

After loading wallet, you'll see:
- **XRD Balance**: Your main Radix tokens
- **Token List**: All other tokens you hold

Balance updates:
- Automatically when trades execute
- Updates every 3 minutes in background

### QR Code Viewer

Hover over the QR icon to show QR code:
- Useful for receiving funds from mobile and not needing to worry about typos. Always double check the address before sending any funds.

### Export Wallet

Saves your wallet to a different file:
1. Go to **Wallet** tab
2. Enter your wallet password
3. Click **Export**
4. Choose new location and filename
5. Wallet is copied with same password

Useful for:
- Creating backups
- Moving wallet to different computer
- Organizing wallet files

---

## Troubleshooting

**"Wrong password" error**
- Double-check password (passwords are case-sensitive)
- Make sure Caps Lock is off
- Try typing slowly to avoid typos
- If truly forgotten, you'll need your seed phrase

**"Can't find wallet file"**
- Check Documents/Radix folder
- Search computer for `wallet name.json`
- If file is lost, restore from seed phrase

**"Balance shows 0 but I have funds"**
- Wait 3 minutes for network sync
- Check your address on Radix Dashboard to verify funds are there
- If Dashboard shows funds but Radbot doesn't, restart Radbot

**"Can't sign transactions"**
- Make sure password is in the password field
- Try unloading and reloading wallet
- Check that wallet file hasn't been moved/deleted
- Verify you have at least 2-3 XRD for transaction fees

**"Lost my seed phrase and forgot password"**
- Sorry, there's no recovery option
- This is how cryptocurrency security works
- Start with a new wallet and be more careful with seed phrases

---

## FAQ

**Q: Can Radbot steal my tokens?**

A: No. Radbot is local software running on YOUR computer. Your wallet file never leaves your machine. All trades happen through official Radix APIs. You can verify this by checking the source code (it's open source).

**Q: What if someone hacks my computer while Radbot is running?**

A: They could potentially access your password from RAM. This is why we recommend:
- Keep antivirus updated
- Don't visit sketchy websites
- Use a dedicated trading wallet with limited funds
- Close Radbot when not actively trading

**Q: Should I give Radbot my hardware wallet?**

A: No! Hardware wallets (Ledger, etc.) are for long-term storage. Use a software (hot) wallet for Radbot. Keep most funds in hardware (cold) wallet, trade with smaller amounts in software wallet.

**Q: Can I run multiple wallets simultaneously?**

A: No, RadBot only supports one active wallet at a time. You can switch wallets by unloading one and loading another. You can however run multiple instances of Radbot on the same machine. DON'T USE THE SAME WALLET!

**Q: What happens if I move my wallet file with Radbot is running?**

A: Radbot will error when trying to use it. Just re-load the wallet from its new location - Radbot will update the path automatically.

**Q: Is my seed phrase stored anywhere in Radbot?**

A: No. Seed phrases are only shown once during wallet creation, then never again. Radbot only stores the wallet file path, not the seed phrase or private keys. Your private key is stored, encrypted with your password, in the `wallet name.json` file

---

## Emergency Procedures

### If You Think Your Wallet Is Compromised

1. **Immediately close Radbot**
2. **Create new wallet** with new seed phrase
3. **Transfer all funds** from old wallet to new wallet using Radix Mobile Wallet
4. **Never use old wallet again**

### If Your Computer Crashes During a Trade

1. **Don't panic** - blockchain transactions are atomic (they complete or fail, no in-between)
2. **Restart computer and Radbot**
3. **Load wallet** and check Active Trades tab
4. **Check Trade History** - last trade will show as complete or not executed
5. If trade shows as "pending" for 5+ minutes, check Radix Dashboard for transaction status

### If You Need to Restore from Seed Phrase

1. Open Radbot
2. Set wallet password (can be different from before)
3. Click **Import Wallet**
4. Enter 24-word seed phrase (exact order, lowercase, space separated)
5. Save wallet file

Remember: Your funds exist on the Radix ledger, not in Radbot. The wallet file is just a key to access them.
