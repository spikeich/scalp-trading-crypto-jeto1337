# Changelog

## 1.1.0 (2026-11-10)

A full review of the repo. What changed:

- **scalp-market / paper.py: the fill rule was wrong.** A limit buy only filled when
  the candle's range contained the entry, so a price that was already below the limit
  left the order "cancelled" and hid the loss. Now a buy fills when the price is at or
  below the entry (a sell, at or above). A stop touched on the fill candle counts (the
  price passes the entry before it can reach the stop); a target on that candle does not.
- **Trades and sessions can cross UTC midnight** (21:00 in Argentina). entry.json and
  plan.json carry full times (`open_at`, `entry_at`, `flat_at`); a free session
  (`--session utc --open HH:MM`) stays current after midnight until it expires.
- **scalp-timemachine: every number also after Binance fees**, with its own verdict.
  At a 0.25 % stop a 2R win is worth +1.84R and a loss costs 1.28R, so the target has
  to come first in 41 % of the decided replays, not 33 %.
- **scalp-timemachine keeps 3 hours of each session** (2 of entries, 1 to hold the last
  ones), so a late entry is replayed to its real time stop. `--open` replaces
  `--window-utc`; `--confirm` (2) for plans given as flags.
- **scalp-alerts: each closed minute is judged once and in order.** Before, a look every
  20 seconds judged the same candle several times, which could ring a target on the fill
  candle; and two failed looks in a row could skip a minute.
- **scalp-exit:** the time stop is entry + hold, always (it was cut short near the end of
  a free session); `--flat-by` is checked.
- **scalp-market / scan.py:** the candidates are the liquid coins (over 1,000 M USD a
  day), as in scalp-scanner; it used to call BTC "too quiet to scalp". The side bias is
  labelled as an untested rule of thumb.
- **scalp-social-info:** Bitcoin fees are no longer "very high" on an idle network (a
  fast fee under 5 sat/vB is always normal); `calendar --now`.
- **Tests:** 113 offline cases that need no network (`--offline-only`), including
  midnight crossings and the two fill rules.

## 1.0.0 (2026-11-06)

First version: eight scalping skills, the 480-configuration research and the tests.
