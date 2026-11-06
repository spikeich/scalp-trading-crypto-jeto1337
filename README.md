# Scalp trading crypto · jeto1337

**English** · [Español](README.es.md)

Eight Claude skills to practise **crypto scalping on 1-minute candles**: check
the news and the blockchain first, find the coins breaking their first 5
minutes at the London or Wall Street open, time the entry, set a tight stop
and a time stop, size the trade to your risk with up to 10x isolated leverage,
replay it 10,000 times, and paper-trade it with Binance fees.

**Read this first: in our tests, scalping lost money after fees.** Four weeks
of 1-minute candles, 480 configurations, not one made money in both halves of
the sample. These skills are a simulator to practise and measure honestly,
not a money machine. See [What the data showed](#what-the-data-showed).

Free, MIT, no signup, no API key. Plain Python, standard library only.
**Nothing here trades for you**: no skill ever sends an order to an exchange.

Sister repo for day trading on 5-minute candles:
[skill-cryptos-jeto1337](https://github.com/spikeich/skill-cryptos-jeto1337).
Both can be installed together: these skills are named `scalp-*`.

## Install

In Claude Code, as a plugin:

```
/plugin marketplace add spikeich/scalp-trading-crypto-jeto1337
/plugin install scalp-trading-crypto-jeto1337@scalp-trading-crypto-jeto1337
```

Or copy the folders:

```bash
git clone https://github.com/spikeich/scalp-trading-crypto-jeto1337.git
cp -r scalp-trading-crypto-jeto1337/scalp-* ~/.claude/skills/
```

They need Python 3.8+ and outbound access to `query1.finance.yahoo.com`,
`query2.finance.yahoo.com` and `api.coingecko.com`, plus `mempool.space` and
`eth.blockscout.com` for the blockchain and `www.theguardian.com`,
`rss.nytimes.com` and `feeds.bbci.co.uk` for the news.

The skills were written in Spanish (their author is Argentine): the scripts
print Spanish, and Claude answers you in whatever language you write in.

## The eight skills

| command | what it does |
| --- | --- |
| `/scalp-social-info` | **First, always.** News verified against 5 reliable sources with dates, on-chain proof of transactions, the state of the Bitcoin and Ethereum networks, and the calendar: no new scalps from 15 minutes before an event to 15 minutes after. |
| `/scalp-scanner` | **What is breaking.** The most liquid coins only (over 1,000 M USD a day), breaking the first 5 minutes of the London or Wall Street open with 2 one-minute closes in a row. |
| `/scalp-entry` | **When to get in.** Candle by candle, the moment 2 one-minute closes in a row land outside the range or a level. Entries expire 2 hours after the open. |
| `/scalp-exit` | **Where to get out.** A 0.25 % stop, a 2R target and a 20-minute time stop by default, with R net of Binance fees and the liquidation price for your leverage. |
| `/scalp-timemachine` | **Does it have an edge?** 10,000 replays of the next 20 minutes from the coin's own 1-minute candles of the last 4 weeks, plus the same rule on every past day. |
| `/scalp-risk` | **Does it fit your limits?** 0.5 % risk a trade, up to 10x isolated, net R of at least 1.2, one scalp at a time, the day ends after 3 losses, a signal older than 3 minutes is stale. Prints the order to type into Binance by hand. |
| `/scalp-alerts` | **While it is open.** Entry filled, stop, target, a limit that never filled, time to get out, from the last 1-minute candle's high and low every 20 seconds. |
| `/scalp-market` | **Size and paper trading.** The position size from your risk (not your leverage), and a paper trade of the plan on real 1-minute candles with fees, in USD. |

## How they fit together

```
/scalp-social-info  news, blockchain, calendar: is this a moment to scalp at all?
/scalp-scanner      what broke the first 5 minutes
/scalp-entry        the exact candle to get in        -> trader/entry.json
/scalp-exit         stop, target, time stop           -> trader/plan.json
/scalp-timemachine  does that plan have an edge?
/scalp-risk         does it fit my limits? size, and the order for Binance
/scalp-alerts       watch it while it is open
/scalp-market       paper-trade it with fees
```

## Leverage, honestly

Leverage does not change what you lose: the stop does. With 3,000 USD, 0.5 %
risk and a 0.25 % stop the position is about 6,000 USD and the stop costs
15 USD whether you use 5x, 10x or 20x. Leverage only decides how much margin is
locked and where the liquidation sits:

| leverage | margin locked | liquidation | if the stop fills |
| --- | --- | --- | --- |
| 5x | 1,200 USD | ~19 % away | -15 USD |
| 10x | 600 USD | ~9.5 % away | -15 USD |
| 20x | 300 USD | ~4.5 % away | -15 USD |
| 50x | 120 USD | ~1.5 % away | -15 USD |

The trap is using leverage to make the position bigger. `/scalp-risk` caps it
at 10x and refuses a plan whose liquidation is closer than twice the stop.

## What the data showed

`research/bt.py`: 4 weeks of 1-minute candles (10 October to 5 November 2026)
for BTC, ETH, SOL, XRP and DOGE, the London and New York opens, Monday to
Friday, entries in the first 2 hours. 480 configurations: opening ranges of 5
and 15 minutes, rolling 15-minute ranges, fading failed breaks, 1 to 3
confirmation closes, stops of 0.15 to 0.35 % or the range's far side, targets
of 1.5R to 3R, time stops of 15 and 30 minutes, market or limit entries. Each
was picked on the first two weeks and judged on the last two.

| | without fees | with Binance fees |
| --- | --- | --- |
| average per trade, weeks 1-2 | +0.08 R | **-0.27 R** |
| average per trade, weeks 3-4 | -0.03 R | **-0.39 R** |
| configurations that made money in both halves | 96 of 480 | **0 of 480** |

- **Fees eat everything.** At a 0.25 % stop, Binance's round trip costs about
  0.3 R a trade. Without fees the setups were near break-even; with fees none
  survived.
- **The best of the first half lost in the second.** The top configuration
  made +24 R in weeks 1-2 and lost -29 R in weeks 3-4: luck, not an edge.
- **Limit orders help, but not enough.** They lose a little less.

Four weeks is a short sample, and Yahoo's candles are not Binance's order book
(no spread, no queue). The direction of the result is clear anyway: retail
scalping fights the fees first and the market second.

Reproduce it:

```bash
cd research
python3 fetch1m.py BTC-USD ETH-USD SOL-USD XRP-USD DOGE-USD
python3 bt.py
python3 bt.py --no-fees
```

## Sessions

| session | opens | UTC (northern winter) | the scalping window |
| --- | --- | --- | --- |
| `europa` | 08:00 London | 08:00 | the first 2 hours |
| `wallstreet` | 09:30 New York | 14:30 | the first 2 hours |

Each day is worked out with its own daylight saving offsets.

## Tests

`python3 tests/run_all.py --twice` runs every command, the offline ones twice,
and checks both passes print the same thing. The live ones need the network.

## Credits

Built from [skill-cryptos-jeto1337](https://github.com/spikeich/skill-cryptos-jeto1337),
whose scanner, entry, exit, time machine, risk and alerts skills are crypto
adaptations of the `trader-*` skills in
[Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill)
(MIT). Its copyright notice is kept in `LICENSE-day-trader-skill`.

## Disclaimer

This is data analysis and a simulator, not financial advice. Leveraged trading
can lose everything you put in, and in our tests scalping lost money after
fees. Practise in your exchange's demo mode first.
