"""Weekly report generator — produces HTML summary of market intelligence."""

import json
from datetime import datetime, timedelta

import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.market_data.morning_brief import MorningBriefService

logger = structlog.get_logger()


class WeeklyReportGenerator:
    """Generates a weekly market intelligence report as HTML."""

    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.redis = redis

    async def generate_html(self) -> str:
        """Generate the weekly report as HTML string."""
        brief_service = MorningBriefService(self.db, self.redis)
        brief = await brief_service._compute_brief()

        now = datetime.utcnow()
        week_start = (now - timedelta(days=7)).strftime("%B %d")
        week_end = now.strftime("%B %d, %Y")

        # Sort commodities by absolute week change for top movers
        commodities = brief.get("commodities", [])
        top_movers = sorted(
            [c for c in commodities if c.get("week_change_pct") is not None],
            key=lambda c: abs(c["week_change_pct"]),
            reverse=True,
        )[:10]

        buy_windows = [c for c in commodities if c.get("signal") == "BUY"]
        wait_signals = [c for c in commodities if c.get("signal") == "WAIT"]

        currencies = brief.get("currencies", [])
        shipping = brief.get("shipping", [])

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AHT Weekly Market Intelligence — {week_end}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #1a1a2e; background: #f8f9fa; }}
h1 {{ color: #1a1a2e; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }}
h2 {{ color: #374151; margin-top: 30px; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
th {{ background: #f3f4f6; font-weight: 600; font-size: 12px; text-transform: uppercase; color: #6b7280; }}
.positive {{ color: #10b981; }}
.negative {{ color: #ef4444; }}
.signal-buy {{ background: #dcfce7; color: #166534; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 12px; }}
.signal-wait {{ background: #fef3c7; color: #92400e; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 12px; }}
.signal-hold {{ background: #f3f4f6; color: #374151; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 12px; }}
.footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px; }}
.alert {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; margin: 10px 0; border-radius: 4px; }}
.opportunity {{ background: #ecfdf5; border-left: 4px solid #10b981; padding: 12px 16px; margin: 10px 0; border-radius: 4px; }}
</style>
</head>
<body>
<h1>AHT Weekly Market Intelligence</h1>
<p style="color: #6b7280;">{week_start} — {week_end}</p>

<h2>Top Movers This Week</h2>
<table>
<tr><th>Commodity</th><th>Price (USD)</th><th>7d Change</th><th>30d Change</th><th>Signal</th></tr>
"""
        for c in top_movers:
            wk = c.get("week_change_pct")
            mo = c.get("month_change_pct")
            wk_cls = "positive" if wk and wk < 0 else "negative" if wk and wk > 0 else ""
            mo_cls = "positive" if mo and mo < 0 else "negative" if mo and mo > 0 else ""
            sig = c.get("signal", "HOLD")
            sig_cls = f"signal-{sig.lower()}"
            html += f"""<tr>
<td>{c['commodity_name']}</td>
<td>${c.get('current_price_usd', 'N/A')}</td>
<td class="{wk_cls}">{wk:+.1f}%</td>
<td class="{mo_cls}">{mo:+.1f}%</td>
<td><span class="{sig_cls}">{sig}</span></td>
</tr>
"""

        html += "</table>"

        # Buy Windows
        if buy_windows:
            html += "<h2>Active Buy Windows</h2>"
            for c in buy_windows:
                html += f"""<div class="opportunity">
<strong>{c['commodity_name']}</strong> — ${c.get('current_price_usd', 'N/A')}/{c.get('unit', '')}
(below 90d MA by {abs(((c.get('current_price_usd', 0) - (c.get('ma_90d') or 0)) / (c.get('ma_90d') or 1)) * 100):.1f}%)
</div>"""

        # Wait Signals
        if wait_signals:
            html += "<h2>Hold / Wait Signals</h2>"
            for c in wait_signals:
                html += f"""<div class="alert">
<strong>{c['commodity_name']}</strong> — ${c.get('current_price_usd', 'N/A')}/{c.get('unit', '')}
(above 90d MA — consider waiting for pullback)
</div>"""

        # Currencies
        if currencies:
            html += """<h2>Currency Monitor</h2>
<table><tr><th>Pair</th><th>Rate</th><th>Week Change</th><th>Trend</th></tr>"""
            for cur in currencies:
                wk = cur.get("week_change_pct")
                wk_str = f"{wk:+.1f}%" if wk is not None else "N/A"
                html += f"""<tr>
<td>{cur.get('pair', cur.get('commodity_name', ''))}</td>
<td>{cur.get('rate', cur.get('current_price_usd', 'N/A'))}</td>
<td>{wk_str}</td>
<td>{cur.get('trend', cur.get('trend_90d', 'flat'))}</td>
</tr>"""
            html += "</table>"

        html += f"""
<div class="footer">
<p>Generated by AHT Intelligence Platform on {now.strftime('%Y-%m-%d %H:%M UTC')}</p>
<p>Data sources: World Bank, IMF, FRED, ExchangeRate-API</p>
</div>
</body>
</html>"""

        return html
