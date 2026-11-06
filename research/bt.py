"""Scalping backtest on 1-minute Yahoo candles, with Binance futures fees.

    python3 fetch1m.py BTC-USD ETH-USD SOL-USD XRP-USD DOGE-USD   # ~28 days of 1-minute candles
    python3 bt.py                     # 480 configurations, first half vs second half
    python3 bt.py --no-fees           # the same without fees

Setups, at the London (08:00) and New York (09:30) opens, Monday to Friday, entries in
the first 2 hours, one coin at a time:
  orb    the first M minutes' range (5 or 15), C closes in a row outside (1, 2, 3)
  rango  a break of the last 15 candles' range, C closes in a row outside
  fade   a close outside the last 15 candles' range, then back inside: trade back in
Stops: 0.15 / 0.25 / 0.35 % or the far side of the range; targets 1.5R / 2R / 3R;
time stop 15 or 30 minutes; entry by market (taker) or limit (maker).
Fees: entry taker 0.05 % or maker 0.02 %, stop taker 0.05 % + 0.01 % slippage, target
maker 0.02 %, time exit taker 0.05 %. A candle that touches the stop and the target
counts as the stop. The configurations are picked on the first half of the days and
judged on the second half.
"""
import argparse, json, datetime as dt, statistics as st, os
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE"]
ap = argparse.ArgumentParser()
ap.add_argument("--data", default=".", help="folder with SYM_1m.json from fetch1m.py")
ap.add_argument("--no-fees", action="store_true")
ARGS = ap.parse_args()
TAKER, MAKER, SLIP = (0.0, 0.0, 0.0) if ARGS.no_fees else (0.05, 0.02, 0.01)   # % of notional

def _nth_sunday(y, m, n):
    d = dt.date(y, m, 1); d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)

def _last_sunday(y, m):
    d = dt.date(y, m + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)

def opens(day):
    """London 08:00 and New York 09:30, in UTC, with each day's own daylight time."""
    bst = _last_sunday(day.year, 3) <= day < _last_sunday(day.year, 10)
    edt = _nth_sunday(day.year, 3, 2) <= day < _nth_sunday(day.year, 11, 1)
    lon = dt.datetime(day.year, day.month, day.day, 7 if bst else 8)
    ny = dt.datetime(day.year, day.month, day.day, 13 if edt else 14, 30)
    return {"londres": lon, "nuevayork": ny}

def load(sym):
    d = json.load(open(os.path.join(ARGS.data, sym + "_1m.json")))
    return {t: (o, h, l, c) for t, o, h, l, c in zip(d["t"], d["o"], d["h"], d["l"], d["c"])}

DATA = {s: load(s) for s in COINS}
T0 = min(min(d) for d in DATA.values()); T1 = max(max(d) for d in DATA.values())
DAYS = [dt.date.fromtimestamp(T0) + dt.timedelta(days=i) for i in range(1, 40)]
DAYS = [d for d in DAYS if dt.datetime(d.year, d.month, d.day, 23).timestamp() < T1 + 7200]

def ts(x):
    return int(x.replace(tzinfo=dt.timezone.utc).timestamp())

def window(bars, start, minutes):
    out = []
    for k in range(minutes):
        b = bars.get(ts(start) + 60 * k)
        if b is None:
            return None if k < 5 else out
        out.append(b)
    return out

def manage(w, i, side, entry, stop, target, tmax, fee_in):
    """from bar i+1 on; -> net % of notional, exit kind"""
    for k in range(i + 1, min(len(w), i + 1 + tmax)):
        o, h, l, c = w[k]
        if side > 0:
            if l <= stop: return (stop - entry) / entry * 100 - fee_in - TAKER - SLIP, "stop"
            if h >= target: return (target - entry) / entry * 100 - fee_in - MAKER, "obj"
        else:
            if h >= stop: return (entry - stop) / entry * 100 - fee_in - TAKER - SLIP, "stop"
            if l <= target: return (entry - target) / entry * 100 - fee_in - MAKER, "obj"
    k = min(len(w) - 1, i + tmax)
    c = w[k][3]
    return side * (c - entry) / entry * 100 - fee_in - TAKER, "tiempo"

def trades_for(w, cfg):
    setup, m, conf, stopk, R, tmax, fee_in = cfg
    out, i, busy_until = [], 0, -1
    if setup == "orb":
        hi = max(b[1] for b in w[:m]); lo = min(b[2] for b in w[:m])
        up = dn = 0
        for i in range(m, min(len(w), 120)):
            c = w[i][3]
            up = up + 1 if c > hi else 0
            dn = dn + 1 if c < lo else 0
            if up >= conf or dn >= conf:
                side = 1 if up >= conf else -1
                out.append((i, side, c, hi, lo)); break
    else:
        L = 15
        i = L
        while i < min(len(w), 120):
            if i <= busy_until: i += 1; continue
            seg = w[i - L:i]
            hi = max(b[1] for b in seg); lo = min(b[2] for b in seg)
            if setup == "rango":
                ok_up = all(w[i + j][3] > hi for j in range(conf) if i + j < len(w)) and i + conf - 1 < len(w)
                ok_dn = all(w[i + j][3] < lo for j in range(conf) if i + j < len(w)) and i + conf - 1 < len(w)
                if (ok_up or ok_dn) and (i == 0 or (w[i - 1][3] <= hi and w[i - 1][3] >= lo)):
                    k = i + conf - 1
                    out.append((k, 1 if ok_up else -1, w[k][3], hi, lo)); busy_until = k + 5
                    i = k + 1; continue
            else:   # fade: bar i closes outside, bar i+1 closes back inside -> opposite
                if i + 1 < len(w) and w[i][3] > hi and lo <= w[i + 1][3] <= hi:
                    out.append((i + 1, -1, w[i + 1][3], max(hi, w[i][1]), lo)); busy_until = i + 6; i += 2; continue
                if i + 1 < len(w) and w[i][3] < lo and lo <= w[i + 1][3] <= hi:
                    out.append((i + 1, 1, w[i + 1][3], hi, min(lo, w[i][2]))); busy_until = i + 6; i += 2; continue
            i += 1
    res = []
    for i, side, e, hi, lo in out:
        if stopk == "far":
            stop = lo if side > 0 else hi
            if setup == "fade":
                stop = (lo if side > 0 else hi)
            dist = abs(e - stop) / e * 100
            if not 0.08 <= dist <= 0.8: continue
        else:
            dist = stopk
            stop = e * (1 - side * dist / 100)
        target = e * (1 + side * R * dist / 100)
        net, kind = manage(w, i, side, e, stop, target, tmax, fee_in)
        res.append((net / dist, kind))
    return res

def run(cfg, days, sessions=("londres", "nuevayork"), weekdays=True):
    rs = []
    for d in days:
        if weekdays and d.weekday() >= 5: continue
        for sname in sessions:
            start = opens(d)[sname]
            for s in COINS:
                w = window(DATA[s], start, 150)
                if not w or len(w) < 60: continue
                rs += [r for r, _ in trades_for(w, cfg)]
    return rs

def summ(rs):
    if not rs: return (0, 0, 0, 0)
    return (len(rs), sum(1 for r in rs if r > 0) / len(rs), st.mean(rs), sum(rs))

half = len(DAYS) // 2
A, B = DAYS[:half], DAYS[half:]
grid = []
for setup, m in (("orb", 5), ("orb", 15), ("rango", 15), ("fade", 15)):
    for conf in ((1, 2, 3) if setup != "fade" else (1,)):
        for stopk in (0.15, 0.25, 0.35, "far"):
            for R in (1.5, 2, 3):
                for tmax in (15, 30):
                    for fee_in, fee_name in ((TAKER, "mercado"), (MAKER, "limite")):
                        grid.append(((setup, m, conf, stopk, R, tmax, fee_in), fee_name))
rows = []
for cfg, fee_name in grid:
    a, b = summ(run(cfg, A)), summ(run(cfg, B))
    rows.append((cfg, fee_name, a, b))
json.dump([(list(c), f, a, b) for c, f, a, b in rows], open("grid%s.json" % ("_nofees" if ARGS.no_fees else ""), "w"))
print("dias", DAYS[0], "->", DAYS[-1], "| mitad A", A[0], "-", A[-1], "| mitad B", B[0], "-", B[-1])
rows.sort(key=lambda r: -r[2][2] if r[2][0] >= 20 else 99)
print("\nMejores 15 en la mitad A (>=20 operaciones), y cómo les fue en la mitad B:")
for cfg, f, a, b in rows[:15]:
    print("%-6s m%-2d c%d stop %-5s %sR %2dmin %-7s | A: %3d op %3.0f%% %+.3fR/op %+6.1fR | B: %3d op %3.0f%% %+.3fR/op %+6.1fR"
          % (cfg[0], cfg[1], cfg[2], cfg[3], cfg[4], cfg[5], f, a[0], 100*a[1], a[2], a[3], b[0], 100*b[1], b[2], b[3]))
allr = [r for r in rows if r[2][0] >= 20]
print("\nconfiguraciones con >=20 op en A:", len(allr), "| positivas en A:", sum(1 for r in allr if r[2][2] > 0),
      "| positivas en A y B:", sum(1 for r in allr if r[2][2] > 0 and r[3][2] > 0))
print("promedio de todas en A %+.3fR/op, en B %+.3fR/op" % (st.mean(r[2][2] for r in allr), st.mean(r[3][2] for r in allr if r[3][0])))
