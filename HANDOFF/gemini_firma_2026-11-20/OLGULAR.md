# Facts (do not invent numbers; if a number is missing write "unknown")
User: Turkey resident, needs a trading BOT (mandatory), budget ~$50 (question: what if $100), wants first prop payout within ~30 days.
Portfolio (backtested 2012-2026, Maven-measured cost, preregistered): Sweep (US100, ~19 trades/yr, +0.7R/trade since 2022),
NB noise band NQ (~4.2 trades/week, small edge), BTC 21-23 UTC (small edge), Donchian XAU 1H, B7 IBS NQ, month-turn. Risk target 0.5%/trade.
No new edge found in 3 search rounds (34+ hypotheses rejected). Execution never tested: user has placed 0 orders. No live/demo bot yet.
Costs: all sims use Maven spreads; other firms' spreads NOT measured. Measuring tool works on any MT5 account (needs a free trial/demo login).

Candidates (official pages 2026-11-18..20):
1) FundedNext Stellar Instant 2K $41.99 (code NOVINS ends Nov 22). 6% trailing (locks), no daily limit, no consistency, max open risk 3%
   (stop distance + floating loss; breach = account ends), news +-5min profit 40% counted, weekends allowed, EA paid add-on (price unknown),
   Telegram-integrated EA banned, same EA copy across multiple FN accounts banned. Free MT5 trial exists (official).
   Min-lot problem at 2K: NB trade risk 1.49% (target 0.5%), Donchian XAU 1.59% (max 21%), B7 and month-turn ~6% (impossible).
   Sim x1 (Sweep+NB min lot+BTC): first payout median 21 days, 12-month net median $102, loss prob 9%; zero-edge control -$32, 63% loss.
2) FN Stellar 2-Step 6K $34.99 (NOVSTR): 8%+5% targets, daily 5%, max 10% static, min 5 days; first payout 21 days after funded.
   Sim x3: 132 days, $414, 8% loss; x2: 175d, $311, 18%.
3) FN 1-Step 6K $65.99: sim x3 77d/$479/8% (risk-sized), current lot x3 43d/$730/9%.
4) FN Instant 5K $104.99 (NOVINS): sim ~18-21 days first payout, 12-mo median ~$251-273, loss ~9-22% (two sim versions).
   At 5K, NB risk ~0.6%, Donchian ~0.64% per trade (fits target better than 2K).
5) Blueberry Instant Elite 2.5K: price NOT official (~$100 list, ~$50 with coupon claim). 10% trailing lock, no daily, no consistency,
   1.5% per trade idea, min 5 active days at 0.5%, payout every 14 days, 80%, weekends ok, high-impact news +-2min banned, MT5.
   EA only if own + disclosed + written consent. Turkey not on restricted list (list titled for evaluations). No official prop trial;
   Blueberry Markets broker MT5 demo exists (same spreads? unknown). NOT simulated.
6) Instant Funding Evolve 10K ~$49 (not official): 1-phase 6% target + 5 profitable days, 4% EOD trailing, 40% best-day,
   NO overnight/weekend holding, payout min $250, max 50% of profit per request, own EA allowed, MT5. Turkey unclear (one directory says restricted).
   Sim (intraday set): first payout 178 days, $438, 26% loss.
Rejected earlier: Maven 2-Step (EA banned), FXIFY instant (EA banned), FTMO (weekend gap rule, price), NLF, Blue Guardian (trust).
Black Friday Nov 27: most firms had not published codes yet.
