"""
Web Dashboard Service for RadBot.

Lightweight aiohttp server providing a read-only remote dashboard.
Configured via advanced_config.json → web_dashboard section.
Disabled by default; requires a password to be set before it will start.
"""
import asyncio
import json
import logging
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from aiohttp import web

from config.advanced_config import AdvancedConfig
from config.paths import DATABASE_PATH

logger = logging.getLogger(__name__)

# Session lifetime: 24 hours
_SESSION_TTL = 86400


class WebDashboardService:
    """Aiohttp web server for remote read-only dashboard access."""

    def __init__(self):
        self.config = AdvancedConfig()
        self.enabled = self.config.get('web_dashboard', 'enabled', False)
        self.port = int(self.config.get('web_dashboard', 'port', 8585))
        self.password = str(self.config.get('web_dashboard', 'password', ''))
        self.poll_interval = int(self.config.get('web_dashboard', 'poll_interval_seconds', 120))

        self._sessions: Dict[str, float] = {}   # token → expiry epoch
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self):
        """Start the web dashboard in a daemon thread."""
        if not self.enabled:
            logger.info("Web dashboard is disabled (web_dashboard.enabled = false)")
            return

        if not self.password:
            logger.warning(
                "Web dashboard enabled but no password set — refusing to start. "
                "Set web_dashboard.password in config/advanced_config.json"
            )
            return

        self._thread = threading.Thread(
            target=self._run_server, daemon=True, name="WebDashboard"
        )
        self._thread.start()
        logger.info("Web dashboard starting on port %d", self.port)

    def stop(self):
        """Gracefully shut down the server."""
        if self._loop and self._runner:
            future = asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop)
            try:
                future.result(timeout=5)
            except Exception:
                pass
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("Web dashboard stopped")

    async def _shutdown(self):
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()

    def _run_server(self):
        """Entry point for the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_app())
        self._loop.run_forever()

    async def _start_app(self):
        app = web.Application()
        app.router.add_get('/', self._handle_page)
        app.router.add_post('/login', self._handle_login)
        app.router.add_post('/logout', self._handle_logout)
        app.router.add_get('/api/dashboard', self._handle_api_dashboard)
        app.router.add_get('/api/trades', self._handle_api_trades)
        app.router.add_get('/api/activity', self._handle_api_activity)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, '0.0.0.0', self.port)
        await self._site.start()
        logger.info("Web dashboard running on http://0.0.0.0:%d", self.port)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def _check_auth(self, request: web.Request) -> bool:
        token = request.cookies.get('radbot_session')
        if not token:
            return False
        expiry = self._sessions.get(token)
        if not expiry or time.time() > expiry:
            self._sessions.pop(token, None)
            return False
        return True

    def _create_session(self) -> str:
        token = secrets.token_hex(32)
        self._sessions[token] = time.time() + _SESSION_TTL
        # Prune expired
        now = time.time()
        self._sessions = {k: v for k, v in self._sessions.items() if v > now}
        return token

    def _verify_password(self, candidate: str) -> bool:
        return secrets.compare_digest(candidate, self.password)

    # ------------------------------------------------------------------
    # Route handlers
    # ------------------------------------------------------------------
    async def _handle_page(self, request: web.Request):
        return web.Response(text=_DASHBOARD_HTML, content_type='text/html')

    async def _handle_login(self, request: web.Request):
        try:
            data = await request.json()
            password = data.get('password', '')
        except Exception:
            return web.json_response({'error': 'Invalid request'}, status=400)

        if self._verify_password(password):
            token = self._create_session()
            resp = web.json_response({
                'success': True,
                'poll_interval': self.poll_interval,
            })
            resp.set_cookie(
                'radbot_session', token,
                max_age=_SESSION_TTL, httponly=True, samesite='Strict'
            )
            return resp

        return web.json_response({'error': 'Invalid password'}, status=401)

    async def _handle_logout(self, request: web.Request):
        token = request.cookies.get('radbot_session')
        if token:
            self._sessions.pop(token, None)
        resp = web.json_response({'success': True})
        resp.del_cookie('radbot_session')
        return resp

    async def _handle_api_dashboard(self, request: web.Request):
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        try:
            data = self._get_dashboard_data()
            return web.json_response(data)
        except Exception as e:
            logger.error("Dashboard API error: %s", e, exc_info=True)
            return web.json_response({'error': 'Internal error'}, status=500)

    async def _handle_api_trades(self, request: web.Request):
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        try:
            data = self._get_trades_data()
            return web.json_response(data)
        except Exception as e:
            logger.error("Trades API error: %s", e, exc_info=True)
            return web.json_response({'error': 'Internal error'}, status=500)

    async def _handle_api_activity(self, request: web.Request):
        if not self._check_auth(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        try:
            data = self._get_activity_data()
            return web.json_response(data)
        except Exception as e:
            logger.error("Activity API error: %s", e, exc_info=True)
            return web.json_response({'error': 'Internal error'}, status=500)

    # ------------------------------------------------------------------
    # Database helpers (read-only, own connection per call)
    # ------------------------------------------------------------------
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(DATABASE_PATH), timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_wallet_context(self, cursor) -> Optional[Dict[str, Any]]:
        """Return active wallet_id and wallet_address, or None."""
        cursor.execute("SELECT active_wallet_id FROM settings WHERE id = 1")
        row = cursor.fetchone()
        if not row or not row['active_wallet_id']:
            return None
        wallet_id = row['active_wallet_id']
        cursor.execute(
            "SELECT wallet_address FROM wallets WHERE wallet_id = ?",
            (wallet_id,)
        )
        wrow = cursor.fetchone()
        if not wrow:
            return None
        return {'wallet_id': wallet_id, 'wallet_address': wrow['wallet_address']}

    # ------------------------------------------------------------------
    # /api/dashboard
    # ------------------------------------------------------------------
    def _get_dashboard_data(self) -> dict:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            ctx = self._get_wallet_context(cursor)
            if not ctx:
                return self._empty_dashboard()

            wallet_id = ctx['wallet_id']
            wallet_address = ctx['wallet_address']

            result = {}
            result.update(self._fetch_statistics(cursor, wallet_id, wallet_address))
            result['token_distribution'] = self._fetch_token_distribution(cursor, wallet_id)
            result['profit_history'] = self._fetch_profit_history(cursor, wallet_id)
            result['volume_data'] = self._fetch_volume_data(cursor, wallet_id)
            result['poll_interval'] = self.poll_interval
            return result
        finally:
            conn.close()

    def _empty_dashboard(self) -> dict:
        return {
            'wallet_value': '0 XRD',
            'profit': '0 XRD',
            'active_trades': 0,
            'win_ratio': '0.00 %',
            'trades_created': 0,
            'trades_cancelled': 0,
            'profitable_trades': 0,
            'unprofitable_trades': 0,
            'tokens_traded': 0,
            'trade_pairs': 0,
            'most_profitable': 'N/A',
            'token_distribution': [],
            'profit_history': [0] * 30,
            'volume_data': [0] * 30,
            'poll_interval': self.poll_interval,
        }

    def _fetch_statistics(self, cursor, wallet_id: int, wallet_address: str) -> dict:
        stats = {
            'wallet_value': '0 XRD',
            'profit': '0 XRD',
            'active_trades': 0,
            'win_ratio': '0.00 %',
            'trades_created': 0,
            'trades_cancelled': 0,
            'profitable_trades': 0,
            'unprofitable_trades': 0,
            'tokens_traded': 0,
            'trade_pairs': 0,
            'most_profitable': 'N/A',
        }

        # Wallet token value
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(CAST(tb.balance AS REAL) * t.token_price_xrd), 0)
                FROM token_balances tb
                JOIN tokens t ON tb.token_address = t.address
                WHERE tb.wallet_id = ?
            """, (wallet_id,))
            row = cursor.fetchone()
            total_xrd = row[0] if row else 0
            stats['wallet_value'] = f"{int(total_xrd)} XRD"
        except Exception as e:
            logger.debug("wallet value query: %s", e)

        # Statistics table
        try:
            cursor.execute("""
                SELECT * FROM statistics WHERE wallet_id = ?
            """, (wallet_id,))
            srow = cursor.fetchone()
            if srow:
                s = dict(srow)
                stats['trades_created'] = s.get('total_trades_created', 0)
                stats['trades_cancelled'] = s.get('total_trades_deleted', 0)
                stats['profitable_trades'] = s.get('winning_trades', 0)
                stats['unprofitable_trades'] = s.get('losing_trades', 0)
                win_rate = s.get('win_rate_percentage', 0) or 0
                stats['win_ratio'] = f"{win_rate:.2f} %"

                total_profit_xrd = s.get('total_profit_xrd', 0) or 0
                total_loss_xrd = s.get('total_loss_xrd', 0) or 0
                if total_profit_xrd != 0 or total_loss_xrd != 0:
                    net = total_profit_xrd - total_loss_xrd
                else:
                    net = (s.get('total_profit', 0) or 0) - (s.get('total_loss', 0) or 0)
                stats['profit'] = f"{'+' if net >= 0 else ''}{net:.2f} XRD"
        except Exception as e:
            logger.debug("statistics query: %s", e)

        # Active trades count
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM trades WHERE wallet_address = ?",
                (wallet_address,)
            )
            stats['active_trades'] = cursor.fetchone()[0]
        except Exception as e:
            logger.debug("active trades count: %s", e)

        # Trade pairs count
        try:
            cursor.execute("SELECT COUNT(*) FROM selected_pairs")
            stats['trade_pairs'] = cursor.fetchone()[0]
        except Exception as e:
            logger.debug("trade pairs count: %s", e)

        # Unique tokens traded
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT tp.base_token AS token FROM trades t
                    JOIN trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
                    WHERE t.wallet_address = ?
                    UNION
                    SELECT tp.quote_token AS token FROM trades t
                    JOIN trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
                    WHERE t.wallet_address = ?
                )
            """, (wallet_address, wallet_address))
            stats['tokens_traded'] = cursor.fetchone()[0]
        except Exception as e:
            logger.debug("tokens traded count: %s", e)

        # Most profitable strategy
        try:
            cursor.execute("""
                SELECT strategy_name, SUM(total_profit) as tp
                FROM trades
                WHERE total_profit IS NOT NULL
                GROUP BY strategy_name
                ORDER BY tp DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row and row['strategy_name']:
                stats['most_profitable'] = row['strategy_name'].title()
        except Exception as e:
            logger.debug("most profitable strategy: %s", e)

        return stats

    def _fetch_token_distribution(self, cursor, wallet_id: int) -> list:
        """Return [{name, percentage, color}, ...] for top tokens."""
        # Predefined colors for known tokens
        colors = {
            "XRD": "#2ecc71", "xUSDC": "#27ae60", "xUSDT": "#1abc9c",
            "HUG": "#f39c12", "FLOOP": "#e67e22", "DFP2": "#e74c3c",
            "ASTRL": "#c0392b", "hETH": "#9b59b6", "hUSDC": "#8e44ad",
            "hUSDT": "#2980b9", "OCI": "#3498db", "xwBTC": "#f1c40f",
            "xwETH": "#95a5a6", "xBTC": "#7f8c8d", "xETH": "#34495e",
        }
        fallback = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6",
                     "#f1c40f", "#e67e22", "#1abc9c", "#16a085"]

        try:
            cursor.execute("""
                SELECT tb.balance, t.symbol, t.token_price_xrd
                FROM token_balances tb
                JOIN tokens t ON tb.token_address = t.address
                WHERE tb.wallet_id = ?
            """, (wallet_id,))
            rows = cursor.fetchall()

            token_values = {}
            total = 0
            for r in rows:
                bal = float(r['balance']) if r['balance'] else 0
                price = float(r['token_price_xrd']) if r['token_price_xrd'] else 0
                val = bal * price
                sym = r['symbol'] or '???'
                token_values[sym] = token_values.get(sym, 0) + val
                total += val

            if total <= 0:
                return []

            sorted_tokens = sorted(token_values.items(), key=lambda x: x[1], reverse=True)
            result = []
            others = 0
            fi = 0
            for i, (sym, val) in enumerate(sorted_tokens):
                if i < 5:
                    pct = (val / total) * 100
                    color = colors.get(sym, fallback[fi % len(fallback)])
                    if sym not in colors:
                        fi += 1
                    result.append({'name': sym, 'percentage': round(pct, 1), 'color': color})
                else:
                    others += val

            if others > 0:
                result.append({
                    'name': 'Others',
                    'percentage': round((others / total) * 100, 1),
                    'color': '#95a5a6'
                })
            return result
        except Exception as e:
            logger.debug("token distribution: %s", e)
            return []

    def _fetch_profit_history(self, cursor, wallet_id: int) -> list:
        """30 days of cumulative profit/loss in XRD."""
        try:
            cursor.execute(
                "SELECT wallet_address FROM wallets WHERE wallet_id = ?",
                (wallet_id,)
            )
            wrow = cursor.fetchone()
            if not wrow:
                return [0] * 30
            wallet_address = wrow['wallet_address']

            cursor.execute("""
                SELECT date, profit_loss_xrd
                FROM daily_statistics
                WHERE wallet_id = ?
                ORDER BY date DESC
                LIMIT 30
            """, (wallet_id,))
            rows = cursor.fetchall()
            stats_by_date = {r['date']: r['profit_loss_xrd'] for r in rows}

            today = datetime.now().date()
            dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
            dates.reverse()

            history = []
            cumulative = 0.0
            for d in dates:
                cumulative += (stats_by_date.get(d, 0) or 0)
                history.append(round(cumulative, 2))
            return history
        except Exception as e:
            logger.debug("profit history: %s", e)
            return [0] * 30

    def _fetch_volume_data(self, cursor, wallet_id: int) -> list:
        """30 days of trading volume in XRD."""
        try:
            cursor.execute("""
                SELECT date, volume_xrd
                FROM daily_statistics
                WHERE wallet_id = ?
                ORDER BY date DESC
                LIMIT 30
            """, (wallet_id,))
            rows = cursor.fetchall()
            stats_by_date = {r['date']: r['volume_xrd'] for r in rows}

            today = datetime.now().date()
            dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
            dates.reverse()

            return [round(stats_by_date.get(d, 0) or 0, 2) for d in dates]
        except Exception as e:
            logger.debug("volume data: %s", e)
            return [0] * 30

    # ------------------------------------------------------------------
    # /api/trades
    # ------------------------------------------------------------------
    def _get_trades_data(self) -> dict:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            ctx = self._get_wallet_context(cursor)
            if not ctx:
                return {'trades': []}

            cursor.execute("""
                SELECT
                    t.trade_id,
                    t.is_active,
                    t.strategy_name,
                    t.trade_amount,
                    t.trade_token_address,
                    t.trade_token_symbol,
                    t.accumulation_token_symbol,
                    t.accumulation_token_address,
                    t.start_amount,
                    t.start_token_address,
                    t.total_profit,
                    t.times_flipped,
                    t.profitable_flips,
                    t.unprofitable_flips,
                    t.current_signal,
                    t.last_signal_updated_at,
                    t.created_at,
                    t.buy_price,
                    t.sell_price,
                    t.trade_volume,
                    t.peak_profit_xrd,
                    tp.base_token,
                    tp.quote_token,
                    base.symbol AS base_token_symbol,
                    quote.symbol AS quote_token_symbol,
                    start_tok.symbol AS start_token_symbol
                FROM trades t
                JOIN trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
                JOIN tokens base ON tp.base_token = base.address
                JOIN tokens quote ON tp.quote_token = quote.address
                JOIN tokens start_tok ON t.start_token_address = start_tok.address
                WHERE t.wallet_address = ?
                ORDER BY t.created_at DESC
            """, (ctx['wallet_address'],))

            trades = []
            for row in cursor.fetchall():
                r = dict(row)
                # Format profit
                try:
                    pf = float(r.get('total_profit', 0) or 0)
                    if abs(pf) < 0.0001 and pf != 0:
                        profit_str = f"{pf:.8f}".rstrip('0').rstrip('.')
                    else:
                        profit_str = f"{pf:.4f}".rstrip('0').rstrip('.')
                    if pf > 0:
                        profit_str = f"+{profit_str}"
                except (ValueError, TypeError):
                    profit_str = "0"
                    pf = 0

                # Format trade amount
                try:
                    amt = float(r.get('trade_amount', 0) or 0)
                    amt_str = f"{amt:.8f}".rstrip('0').rstrip('.')
                except (ValueError, TypeError):
                    amt_str = str(r.get('trade_amount', '0'))

                # Format start amount
                try:
                    start = float(r.get('start_amount', 0) or 0)
                    start_str = f"{start:.8f}".rstrip('0').rstrip('.')
                except (ValueError, TypeError):
                    start_str = str(r.get('start_amount', '0'))

                trades.append({
                    'trade_id': r['trade_id'],
                    'pair': f"{r['base_token_symbol']}-{r['quote_token_symbol']}",
                    'base_symbol': r['base_token_symbol'],
                    'quote_symbol': r['quote_token_symbol'],
                    'strategy': r.get('strategy_name', 'N/A'),
                    'is_active': bool(r.get('is_active', 0)),
                    'current_amount': amt_str,
                    'current_token': r.get('trade_token_symbol', ''),
                    'start_amount': start_str,
                    'start_token': r.get('start_token_symbol', ''),
                    'accumulation_token': r.get('accumulation_token_symbol', ''),
                    'profit': profit_str,
                    'profit_raw': pf,
                    'times_flipped': r.get('times_flipped', 0) or 0,
                    'profitable_flips': r.get('profitable_flips', 0) or 0,
                    'unprofitable_flips': r.get('unprofitable_flips', 0) or 0,
                    'current_signal': r.get('current_signal', 'hold'),
                    'last_signal_at': r.get('last_signal_updated_at', ''),
                    'buy_price': r.get('buy_price', ''),
                    'sell_price': r.get('sell_price', ''),
                    'trade_volume': round(float(r.get('trade_volume', 0) or 0), 2),
                    'peak_profit_xrd': round(float(r.get('peak_profit_xrd', 0) or 0), 4),
                    'created_at': r.get('created_at', ''),
                })

            return {'trades': trades}
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # /api/activity  (recent trade flips — filtered, no sensitive data)
    # ------------------------------------------------------------------
    def _get_activity_data(self) -> dict:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            ctx = self._get_wallet_context(cursor)
            if not ctx:
                return {'activity': []}

            cursor.execute("""
                SELECT
                    th.history_id,
                    th.trade_id_original AS trade_id,
                    th.pair,
                    th.side,
                    th.amount_base,
                    th.amount_quote,
                    th.price,
                    th.usd_value,
                    th.status,
                    th.strategy_name,
                    th.profit,
                    th.profit_usd,
                    th.profit_xrd,
                    th.created_at
                FROM trade_history th
                WHERE th.wallet_address = ?
                  AND th.status = 'SUCCESS'
                ORDER BY th.created_at DESC
                LIMIT 50
            """, (ctx['wallet_address'],))

            activity = []
            for row in cursor.fetchall():
                r = dict(row)
                # Format timestamp
                try:
                    ts = int(r.get('created_at', 0))
                    dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                except (ValueError, TypeError, OSError):
                    dt = str(r.get('created_at', ''))

                activity.append({
                    'trade_id': r.get('trade_id', 0),
                    'pair': r.get('pair', ''),
                    'side': r.get('side', ''),
                    'amount_base': r.get('amount_base', '0'),
                    'amount_quote': r.get('amount_quote', '0'),
                    'price': round(float(r.get('price', 0) or 0), 6),
                    'usd_value': round(float(r.get('usd_value', 0) or 0), 2),
                    'strategy': r.get('strategy_name', ''),
                    'profit': r.get('profit', ''),
                    'profit_usd': round(float(r.get('profit_usd', 0) or 0), 2),
                    'profit_xrd': round(float(r.get('profit_xrd', 0) or 0), 4),
                    'timestamp': dt,
                    'status': r.get('status', ''),
                })

            return {'activity': activity}
        finally:
            conn.close()


# ======================================================================
# Embedded Dashboard HTML (single-page app)
# ======================================================================
_DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Radbot Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
/* ── Reset & Base ─────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#060a1a;--surface:#0d1329;--card:#111a3a;
  --border:#1e293b;--text:#e2e8f0;--muted:#64748b;
  --accent:#00d4ff;--accent2:#e040fb;
  --green:#22c55e;--red:#ef4444;--blue:#0d6efd;
  --radius:12px;
}
html,body{height:100%;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text)}
a{color:var(--accent);text-decoration:none}

/* ── Login ────────────────────────────────────────────────── */
#login-screen{
  display:flex;align-items:center;justify-content:center;height:100vh;
  background:radial-gradient(ellipse at 30% 50%,rgba(0,212,255,.06) 0%,transparent 60%),
             radial-gradient(ellipse at 70% 50%,rgba(224,64,251,.06) 0%,transparent 60%),
             var(--bg);
}
.login-card{
  background:rgba(17,26,58,.85);backdrop-filter:blur(20px);
  border:1px solid var(--border);border-radius:var(--radius);
  padding:40px;width:360px;text-align:center;
}
.login-card h1{font-size:1.6rem;margin-bottom:6px}
.login-card .sub{color:var(--muted);font-size:.85rem;margin-bottom:28px}
.login-card input{
  width:100%;padding:12px 16px;border:1px solid var(--border);border-radius:8px;
  background:var(--surface);color:var(--text);font-size:1rem;outline:none;
  margin-bottom:16px;transition:border .2s;
}
.login-card input:focus{border-color:var(--accent)}
.login-card button{
  width:100%;padding:12px;border:none;border-radius:8px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  color:#fff;font-size:1rem;font-weight:600;cursor:pointer;transition:opacity .2s;
}
.login-card button:hover{opacity:.85}
.login-error{color:var(--red);font-size:.85rem;margin-top:8px;min-height:20px}

/* ── Dashboard Shell ──────────────────────────────────────── */
#dashboard{display:none;min-height:100vh;padding:20px 24px;
  background:radial-gradient(ellipse at 20% 10%,rgba(0,212,255,.04) 0%,transparent 50%),
             radial-gradient(ellipse at 80% 80%,rgba(224,64,251,.04) 0%,transparent 50%),
             var(--bg);
}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.topbar h1{font-size:1.4rem;background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.topbar .meta{display:flex;align-items:center;gap:16px}
.topbar .meta span{color:var(--muted);font-size:.8rem}
.btn-logout{padding:6px 14px;border:1px solid var(--border);border-radius:6px;
  background:transparent;color:var(--muted);cursor:pointer;font-size:.8rem;transition:all .2s}
.btn-logout:hover{border-color:var(--red);color:var(--red)}

/* ── Summary Cards ────────────────────────────────────────── */
.summary-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
.summary-card{
  background:rgba(17,26,58,.7);backdrop-filter:blur(12px);
  border:1px solid var(--border);border-radius:var(--radius);
  padding:18px 20px;transition:border-color .3s;
}
.summary-card:hover{border-color:rgba(0,212,255,.3)}
.summary-card .label{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.summary-card .value{font-size:1.5rem;font-weight:700;margin-top:6px}
.summary-card .value.profit-positive{color:var(--green)}
.summary-card .value.profit-negative{color:var(--red)}

/* ── Chart Grid ───────────────────────────────────────────── */
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
.chart-card{
  background:rgba(17,26,58,.7);backdrop-filter:blur(12px);
  border:1px solid var(--border);border-radius:var(--radius);padding:20px;
}
.chart-card h3{font-size:.95rem;margin-bottom:14px;color:var(--text)}
.chart-card canvas{width:100%!important;max-height:220px}

/* ── Stats + Trades Row ───────────────────────────────────── */
.content-grid{display:grid;grid-template-columns:300px 1fr;gap:16px;margin-bottom:20px}
.stats-card{
  background:rgba(17,26,58,.7);backdrop-filter:blur(12px);
  border:1px solid var(--border);border-radius:var(--radius);padding:20px;
}
.stats-card h3{font-size:.95rem;margin-bottom:16px}
.stat-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(30,41,59,.5)}
.stat-row:last-child{border-bottom:none}
.stat-row .stat-label{color:var(--muted);font-size:.85rem}
.stat-row .stat-value{font-weight:600;font-size:.85rem}

/* ── Trades Table ─────────────────────────────────────────── */
.trades-card{
  background:rgba(17,26,58,.7);backdrop-filter:blur(12px);
  border:1px solid var(--border);border-radius:var(--radius);padding:20px;overflow:auto;
}
.trades-card h3{font-size:.95rem;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:.82rem}
thead th{text-align:left;padding:8px 10px;color:var(--muted);border-bottom:1px solid var(--border);
  font-weight:600;text-transform:uppercase;font-size:.72rem;letter-spacing:.4px}
tbody tr{border-bottom:1px solid rgba(30,41,59,.3);transition:background .15s;cursor:default;position:relative}
tbody tr:hover{background:rgba(0,212,255,.04)}
tbody td{padding:8px 10px;white-space:nowrap}
.pill{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.72rem;font-weight:600}
.pill-active{background:rgba(34,197,94,.15);color:var(--green)}
.pill-paused{background:rgba(239,68,68,.15);color:var(--red)}

/* ── Hover Detail Card ────────────────────────────────────── */
.trade-tooltip{
  display:none;position:fixed;z-index:1000;
  background:rgba(13,19,41,.97);backdrop-filter:blur(16px);
  border:1px solid var(--accent);border-radius:10px;
  padding:16px 20px;width:320px;pointer-events:none;
  box-shadow:0 8px 32px rgba(0,0,0,.5);
}
.trade-tooltip.show{display:block}
.trade-tooltip h4{font-size:.9rem;margin-bottom:10px;color:var(--accent)}
.tt-row{display:flex;justify-content:space-between;padding:3px 0;font-size:.8rem}
.tt-row .tt-label{color:var(--muted)}
.tt-row .tt-value{font-weight:500}

/* ── Activity Log ─────────────────────────────────────────── */
.activity-card{
  background:rgba(17,26,58,.7);backdrop-filter:blur(12px);
  border:1px solid var(--border);border-radius:var(--radius);padding:20px;
}
.activity-card h3{font-size:.95rem;margin-bottom:14px}
.activity-list{max-height:300px;overflow-y:auto}
.activity-item{
  display:flex;align-items:center;gap:12px;padding:8px 0;
  border-bottom:1px solid rgba(30,41,59,.3);font-size:.82rem;
}
.activity-item:last-child{border-bottom:none}
.activity-side{font-weight:700;width:38px;text-align:center;padding:2px 0;border-radius:4px;font-size:.72rem}
.activity-side.BUY{background:rgba(34,197,94,.15);color:var(--green)}
.activity-side.SELL{background:rgba(239,68,68,.15);color:var(--red)}
.activity-details{flex:1;display:flex;justify-content:space-between;align-items:center}
.activity-pair{font-weight:600}
.activity-profit{font-weight:600}
.activity-time{color:var(--muted);font-size:.72rem;width:110px;text-align:right}

/* ── Responsive ───────────────────────────────────────────── */
@media(max-width:900px){
  .summary-row{grid-template-columns:repeat(2,1fr)}
  .chart-grid{grid-template-columns:1fr}
  .content-grid{grid-template-columns:1fr}
}
@media(max-width:600px){
  .summary-row{grid-template-columns:1fr}
  #dashboard{padding:12px}
}

/* ── Empty state ──────────────────────────────────────────── */
.empty-state{text-align:center;padding:40px 20px;color:var(--muted);font-size:.9rem}

/* ── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
</style>
</head>
<body>

<!-- Login Screen -->
<div id="login-screen">
  <div class="login-card">
    <h1>Radbot</h1>
    <div class="sub">Remote Dashboard</div>
    <form id="login-form">
      <input type="password" id="password-input" placeholder="Enter dashboard password" autocomplete="off" autofocus>
      <button type="submit">Sign In</button>
    </form>
    <div class="login-error" id="login-error"></div>
  </div>
</div>

<!-- Dashboard -->
<div id="dashboard">
  <div class="topbar">
    <h1>Radbot Dashboard</h1>
    <div class="meta">
      <span id="last-update">—</span>
      <button class="btn-logout" onclick="doLogout()">Logout</button>
    </div>
  </div>

  <!-- Summary Row -->
  <div class="summary-row">
    <div class="summary-card">
      <div class="label">Wallet Value</div>
      <div class="value" id="s-wallet-value">—</div>
    </div>
    <div class="summary-card">
      <div class="label">Total Profit</div>
      <div class="value" id="s-profit">—</div>
    </div>
    <div class="summary-card">
      <div class="label">Active Trades</div>
      <div class="value" id="s-active-trades">—</div>
    </div>
    <div class="summary-card">
      <div class="label">Win Ratio</div>
      <div class="value" id="s-win-ratio">—</div>
    </div>
  </div>

  <!-- Charts Row -->
  <div class="chart-grid">
    <div class="chart-card">
      <h3>Profit / Loss (30 Days)</h3>
      <canvas id="profit-chart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Wallet Token Distribution</h3>
      <canvas id="distribution-chart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Trading Volume — XRD (30 Days)</h3>
      <canvas id="volume-chart"></canvas>
    </div>
    <div class="chart-card stats-panel">
      <h3>Trade Statistics</h3>
      <div class="stat-row"><span class="stat-label">Trades Created</span><span class="stat-value" id="st-created">0</span></div>
      <div class="stat-row"><span class="stat-label">Trades Deleted</span><span class="stat-value" id="st-cancelled">0</span></div>
      <div class="stat-row"><span class="stat-label">Profitable Trades</span><span class="stat-value" id="st-profitable" style="color:var(--green)">0</span></div>
      <div class="stat-row"><span class="stat-label">Unprofitable Trades</span><span class="stat-value" id="st-unprofitable" style="color:var(--red)">0</span></div>
      <div class="stat-row"><span class="stat-label">Tokens Traded</span><span class="stat-value" id="st-tokens">0</span></div>
      <div class="stat-row"><span class="stat-label">Trade Pairs</span><span class="stat-value" id="st-pairs">0</span></div>
      <div class="stat-row"><span class="stat-label">Most Profitable</span><span class="stat-value" id="st-best">N/A</span></div>
    </div>
  </div>

  <!-- Trades + Activity -->
  <div class="content-grid" style="grid-template-columns:1fr">
    <div class="trades-card">
      <h3>Active Trades</h3>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Pair</th><th>Strategy</th><th>Position</th>
            <th>Profit</th><th>Flips</th><th>Signal</th><th>State</th>
          </tr>
        </thead>
        <tbody id="trades-body"></tbody>
      </table>
      <div class="empty-state" id="trades-empty" style="display:none">No active trades</div>
    </div>
  </div>

  <div class="activity-card">
    <h3>Recent Activity</h3>
    <div class="activity-list" id="activity-list">
      <div class="empty-state" id="activity-empty">No recent activity</div>
    </div>
  </div>
</div>

<!-- Hover tooltip for trades -->
<div class="trade-tooltip" id="trade-tooltip"></div>

<script>
/* ── State ──────────────────────────────────────────────── */
let pollInterval = 120;
let pollTimer = null;
let profitChart = null, distributionChart = null, volumeChart = null;
let tradesData = [];

/* ── Login ──────────────────────────────────────────────── */
document.getElementById('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const pw = document.getElementById('password-input').value;
  const err = document.getElementById('login-error');
  err.textContent = '';
  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({password: pw})
    });
    const data = await res.json();
    if (res.ok && data.success) {
      pollInterval = data.poll_interval || 120;
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('dashboard').style.display = 'block';
      initCharts();
      refreshAll();
      startPolling();
    } else {
      err.textContent = data.error || 'Invalid password';
    }
  } catch (ex) {
    err.textContent = 'Connection failed';
  }
});

async function doLogout() {
  stopPolling();
  await fetch('/logout', {method: 'POST'});
  document.getElementById('dashboard').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('password-input').value = '';
}

/* ── Polling ────────────────────────────────────────────── */
function startPolling() { pollTimer = setInterval(refreshAll, pollInterval * 1000); }
function stopPolling() { if (pollTimer) clearInterval(pollTimer); pollTimer = null; }

async function refreshAll() {
  try {
    const [dashRes, tradesRes, actRes] = await Promise.all([
      fetch('/api/dashboard'), fetch('/api/trades'), fetch('/api/activity')
    ]);
    if (dashRes.status === 401) { doLogout(); return; }
    const dash = await dashRes.json();
    const trades = await tradesRes.json();
    const act = await actRes.json();
    renderDashboard(dash);
    renderTrades(trades.trades || []);
    renderActivity(act.activity || []);
    document.getElementById('last-update').textContent = 'Updated ' + new Date().toLocaleTimeString();
  } catch (ex) {
    console.error('Refresh error:', ex);
  }
}

/* ── Render Dashboard ───────────────────────────────────── */
function renderDashboard(d) {
  setText('s-wallet-value', d.wallet_value);
  const profitEl = document.getElementById('s-profit');
  profitEl.textContent = d.profit;
  profitEl.className = 'value ' + (d.profit && d.profit.startsWith('+') ? 'profit-positive' : d.profit && d.profit.startsWith('-') ? 'profit-negative' : '');
  setText('s-active-trades', d.active_trades);
  setText('s-win-ratio', d.win_ratio);
  setText('st-created', d.trades_created);
  setText('st-cancelled', d.trades_cancelled);
  setText('st-profitable', d.profitable_trades);
  setText('st-unprofitable', d.unprofitable_trades);
  setText('st-tokens', d.tokens_traded);
  setText('st-pairs', d.trade_pairs);
  setText('st-best', d.most_profitable);
  updateProfitChart(d.profit_history || []);
  updateDistributionChart(d.token_distribution || []);
  updateVolumeChart(d.volume_data || []);
}

function setText(id, val) { document.getElementById(id).textContent = val; }

/* ── Charts ─────────────────────────────────────────────── */
function initCharts() {
  const gridColor = 'rgba(30,41,59,.5)';
  const tickColor = '#64748b';

  // Profit chart (line)
  profitChart = new Chart(document.getElementById('profit-chart'), {
    type: 'line',
    data: { labels: Array.from({length:30},(_,i)=>i+1), datasets: [{
      data: [], fill: true,
      borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,.12)',
      borderWidth: 2, pointRadius: 0, tension: 0.3
    }]},
    options: chartOpts(gridColor, tickColor)
  });

  // Distribution chart (doughnut)
  distributionChart = new Chart(document.getElementById('distribution-chart'), {
    type: 'doughnut',
    data: { labels: [], datasets: [{ data: [], backgroundColor: [], borderWidth: 0 }]},
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { position: 'right', labels: { color: '#e2e8f0', boxWidth: 12, padding: 10, font: {size: 11} }},
      }
    }
  });

  // Volume chart (bar)
  volumeChart = new Chart(document.getElementById('volume-chart'), {
    type: 'bar',
    data: { labels: Array.from({length:30},(_,i)=>i+1), datasets: [{
      data: [], backgroundColor: 'rgba(13,110,253,.6)',
      borderColor: '#0d6efd', borderWidth: 1, borderRadius: 3
    }]},
    options: chartOpts(gridColor, tickColor)
  });
}

function chartOpts(gridColor, tickColor) {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }},
    scales: {
      x: { grid: {color: gridColor}, ticks: {color: tickColor, maxTicksLimit: 10, font:{size:10}}},
      y: { grid: {color: gridColor}, ticks: {color: tickColor, font:{size:10}}}
    }
  };
}

function updateProfitChart(data) {
  profitChart.data.datasets[0].data = data;
  const isNeg = data.length && data[data.length-1] < 0;
  profitChart.data.datasets[0].borderColor = isNeg ? '#ef4444' : '#22c55e';
  profitChart.data.datasets[0].backgroundColor = isNeg ? 'rgba(239,68,68,.12)' : 'rgba(34,197,94,.12)';
  profitChart.update('none');
}

function updateDistributionChart(tokens) {
  distributionChart.data.labels = tokens.map(t => t.name);
  distributionChart.data.datasets[0].data = tokens.map(t => t.percentage);
  distributionChart.data.datasets[0].backgroundColor = tokens.map(t => t.color);
  distributionChart.update('none');
}

function updateVolumeChart(data) {
  volumeChart.data.datasets[0].data = data;
  volumeChart.update('none');
}

/* ── Trades Table ───────────────────────────────────────── */
const tooltip = document.getElementById('trade-tooltip');

function renderTrades(trades) {
  tradesData = trades;
  const tbody = document.getElementById('trades-body');
  const empty = document.getElementById('trades-empty');
  if (!trades.length) { tbody.innerHTML = ''; empty.style.display = 'block'; return; }
  empty.style.display = 'none';
  tbody.innerHTML = trades.map((t, i) => {
    const profitClass = t.profit_raw > 0 ? 'color:var(--green)' : t.profit_raw < 0 ? 'color:var(--red)' : '';
    const stateClass = t.is_active ? 'pill-active' : 'pill-paused';
    const stateText = t.is_active ? 'ACTIVE' : 'PAUSED';
    return `<tr data-idx="${i}" onmouseenter="showTooltip(event,${i})" onmousemove="moveTooltip(event)" onmouseleave="hideTooltip()">
      <td>${t.trade_id}</td>
      <td style="font-weight:600">${t.pair}</td>
      <td>${t.strategy}</td>
      <td>${t.current_amount} ${t.current_token}</td>
      <td style="${profitClass};font-weight:600">${t.profit} ${t.accumulation_token}</td>
      <td>${t.times_flipped}</td>
      <td>${t.current_signal || 'hold'}</td>
      <td><span class="pill ${stateClass}">${stateText}</span></td>
    </tr>`;
  }).join('');
}

function showTooltip(e, idx) {
  const t = tradesData[idx]; if (!t) return;
  const profitStyle = t.profit_raw > 0 ? 'color:var(--green)' : t.profit_raw < 0 ? 'color:var(--red)' : '';
  tooltip.innerHTML = `
    <h4>Trade #${t.trade_id} — ${t.pair}</h4>
    <div class="tt-row"><span class="tt-label">Strategy</span><span class="tt-value">${t.strategy}</span></div>
    <div class="tt-row"><span class="tt-label">State</span><span class="tt-value">${t.is_active ? 'Active' : 'Paused'}</span></div>
    <div class="tt-row"><span class="tt-label">Current Position</span><span class="tt-value">${t.current_amount} ${t.current_token}</span></div>
    <div class="tt-row"><span class="tt-label">Start Position</span><span class="tt-value">${t.start_amount} ${t.start_token}</span></div>
    <div class="tt-row"><span class="tt-label">Accumulating</span><span class="tt-value">${t.accumulation_token}</span></div>
    <div class="tt-row"><span class="tt-label">Profit</span><span class="tt-value" style="${profitStyle}">${t.profit} ${t.accumulation_token}</span></div>
    <div class="tt-row"><span class="tt-label">Peak Profit</span><span class="tt-value">${t.peak_profit_xrd} XRD</span></div>
    <div class="tt-row"><span class="tt-label">Volume</span><span class="tt-value">${t.trade_volume} XRD</span></div>
    <div class="tt-row"><span class="tt-label">Flips</span><span class="tt-value">${t.times_flipped} (${t.profitable_flips}W / ${t.unprofitable_flips}L)</span></div>
    <div class="tt-row"><span class="tt-label">Signal</span><span class="tt-value">${t.current_signal || 'hold'}</span></div>
    <div class="tt-row"><span class="tt-label">Last Signal</span><span class="tt-value">${t.last_signal_at || '—'}</span></div>
    ${t.buy_price ? `<div class="tt-row"><span class="tt-label">Buy Price</span><span class="tt-value">${t.buy_price}</span></div>` : ''}
    ${t.sell_price ? `<div class="tt-row"><span class="tt-label">Sell Price</span><span class="tt-value">${t.sell_price}</span></div>` : ''}
    <div class="tt-row"><span class="tt-label">Created</span><span class="tt-value">${t.created_at || '—'}</span></div>
  `;
  tooltip.classList.add('show');
  moveTooltip(e);
}

function moveTooltip(e) {
  let x = e.clientX + 16, y = e.clientY + 12;
  const w = tooltip.offsetWidth, h = tooltip.offsetHeight;
  if (x + w > window.innerWidth - 10) x = e.clientX - w - 10;
  if (y + h > window.innerHeight - 10) y = e.clientY - h - 10;
  tooltip.style.left = x + 'px'; tooltip.style.top = y + 'px';
}

function hideTooltip() { tooltip.classList.remove('show'); }

/* ── Activity Log ───────────────────────────────────────── */
function renderActivity(items) {
  const container = document.getElementById('activity-list');
  const empty = document.getElementById('activity-empty');
  if (!items.length) { container.innerHTML = ''; container.appendChild(empty); empty.style.display = 'block'; return; }
  empty.style.display = 'none';
  container.innerHTML = items.map(a => {
    const profitColor = a.profit_xrd > 0 ? 'color:var(--green)' : a.profit_xrd < 0 ? 'color:var(--red)' : '';
    const profitText = a.profit || '';
    return `<div class="activity-item">
      <span class="activity-side ${a.side}">${a.side}</span>
      <div class="activity-details">
        <span class="activity-pair">${a.pair}</span>
        <span class="activity-profit" style="${profitColor}">${profitText}</span>
      </div>
      <span class="activity-time">${a.timestamp}</span>
    </div>`;
  }).join('');
}
</script>
</body>
</html>"""
