"""Download ~28 days of 1-minute Yahoo bars in 7-day chunks -> SYM_1m.json {t:[...],o,h,l,c,v}."""
import json, sys, time, urllib.request, urllib.parse
UA = "Mozilla/5.0"
def chunk(sym, p1, p2):
    q = urllib.parse.urlencode({"period1": p1, "period2": p2, "interval": "1m"})
    for host in ("query2", "query1"):
        for attempt in range(3):
            try:
                url = "https://%s.finance.yahoo.com/v8/finance/chart/%s?%s" % (host, sym, q)
                r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))
                return r["chart"]["result"][0]
            except Exception as e:
                print("  retry", sym, host, e, file=sys.stderr); time.sleep(20)
    raise SystemExit("failed " + sym)
now = int(time.time()) // 60 * 60
for sym in sys.argv[1:]:
    rows = {}
    for k in range(4):
        p2 = now - k * 7 * 86400; p1 = p2 - 7 * 86400 + 60
        res = chunk(sym, p1, p2)
        q = res["indicators"]["quote"][0]
        for i, t in enumerate(res.get("timestamp") or []):
            if q["close"][i] is not None and q["high"][i] is not None:
                rows[t] = (q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i] or 0)
        time.sleep(1.5)
    ts = sorted(rows)
    out = {"t": ts, "o": [rows[t][0] for t in ts], "h": [rows[t][1] for t in ts], "l": [rows[t][2] for t in ts],
           "c": [rows[t][3] for t in ts], "v": [rows[t][4] for t in ts]}
    json.dump(out, open(sym.split("-")[0] + "_1m.json", "w"))
    import datetime as dt
    print(sym, len(ts), dt.datetime.utcfromtimestamp(ts[0]), "->", dt.datetime.utcfromtimestamp(ts[-1]))
