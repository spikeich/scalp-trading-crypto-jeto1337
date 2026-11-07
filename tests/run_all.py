#!/usr/bin/env python3
"""Run every command of the 8 scalping skills. Standard library only.

    python3 tests/run_all.py                 # one pass, results in a temporary folder
    python3 tests/run_all.py --twice         # two passes; the offline cases must print the same twice
    python3 tests/run_all.py --only scalp-entry,social --out /tmp/t
    python3 tests/run_all.py --twice --offline-only   # skip the cases that need live prices

Each case: (name, args, expected exit codes, offline?, text that must appear).
Offline cases read the saved candles in tests/data (or pin the clock with --now),
so two passes must print exactly the same. Live cases read Yahoo, CoinGecko and
mempool.space: they only have to run cleanly (the expected exit code, no traceback).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(REPO, "tests", "data")
BTC2D = D + "/BTC-2d1m.json"            # Yahoo 1-minute candles, 5 and 6 November 2026
BTC28 = D + "/BTC-28d1m.json.gz"        # 28 days of them, for the time machine
CH = D + "/chain"
PIZZA = "a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d"
ETHTX = "0x23bbe48f54aadf3ac5f32b0b950df739efa3c700e919b30679152a48e04cd151"
FOUR = ["--source", "Reuters|u|confirma|2026-11-06 13:50", "--source", "CNBC|u|confirma|2026-11-06 13:55",
        "--source", "NPR|u|confirma|2026-11-06 14:00", "--source", "Bloomberg|u|confirma|2026-11-06 13:52"]

MK = REPO + "/scalp-market/"
SC = REPO + "/scalp-scanner/scan.py"
EN = REPO + "/scalp-entry/entry.py"
EX = REPO + "/scalp-exit/exit.py"
TM = REPO + "/scalp-timemachine/timemachine.py"
RK = REPO + "/scalp-risk/risk.py"
AL = REPO + "/scalp-alerts/alerts.py"
SO = REPO + "/scalp-social-info/social.py"
BTC_LONG = ["--symbol", "BTC", "--date", "2026-11-06", "--side", "buy", "--entry", "75783", "--stop", "75593",
            "--target", "76163", "--entry-time", "14:42", "--hold", "20", "--offline", BTC28, "--now",
            "2026-11-06 16:40"]

CASES = [
    # ---- scalp-market
    ("scalp-market size", [MK + "size.py", "--capital", "3000", "--entry", "75783", "--stop", "75593",
                           "--target", "76163"], [0], True, "relación 1.44"),
    ("scalp-market size liquidation", [MK + "size.py", "--capital", "3000", "--entry", "75783", "--stop", "74000",
                                       "--lev", "50"], [0], True, "La liquidación llega antes que el stop"),
    ("scalp-market scan live", [MK + "scan.py"], [0, 1], False, ""),

    # ---- scalp-entry (saved BTC candles of 6 November)
    ("scalp-entry forming", [EN, "check", "BTC", "--offline", BTC2D, "--now", "2026-11-06 14:33"], [1], True,
     "el rango se está formando"),
    ("scalp-entry waiting", [EN, "check", "BTC", "--offline", BTC2D, "--now", "2026-11-06 14:40"], [1], True,
     "ESPERANDO"),
    ("scalp-entry orb wallstreet", [EN, "check", "BTC", "--offline", BTC2D, "--now", "2026-11-06 14:50", "--write"],
     [0], True, "DISPARÓ LARGO: la vela que cerró a las 14:42 UTC"),
    ("scalp-entry orb europa", [EN, "check", "BTC", "--session", "europa", "--offline", BTC2D, "--now",
                                "2026-11-06 09:00"], [0], True, "DISPARÓ CORTO: la vela que cerró a las 08:11 UTC"),
    ("scalp-entry short side", [EN, "check", "BTC", "--side", "short", "--offline", BTC2D, "--now",
                                "2026-11-06 15:10"], [0], True, "DISPARÓ CORTO: la vela que cerró a las 15:05 UTC"),
    ("scalp-entry confirm 1", [EN, "check", "BTC", "--confirm", "1", "--offline", BTC2D, "--now",
                               "2026-11-06 14:50"], [0], True, "DISPARÓ LARGO"),
    ("scalp-entry expired", [EN, "check", "BTC", "--side", "short", "--offline", BTC2D, "--now",
                             "2026-11-06 16:40", "--expire-hours", "0.2"], [1], True, "VENCIDO"),
    ("scalp-entry level", [EN, "check", "BTC", "--setup", "level", "--level", "76000", "--side", "long",
                           "--offline", BTC2D, "--now", "2026-11-06 16:30"], [0, 1], True, "Nivel: 76000"),
    ("scalp-entry bad minutes", [EN, "check", "BTC", "--or-minutes", "0"], [1], True, "between 1 and 60"),
    ("scalp-entry level needs side", [EN, "check", "BTC", "--setup", "level", "--level", "1"], [1], True,
     "--side long"),
    ("scalp-entry utc session", [EN, "check", "BTC", "--session", "utc", "--open", "01:00", "--offline", BTC2D,
                                 "--now", "2026-11-06 03:00"], [0, 1], True, "sesión utc (abre 01:00 UTC)"),
    ("scalp-entry utc needs open", [EN, "check", "BTC", "--session", "utc"], [1], True, "needs --open"),
    ("scalp-entry live", [EN, "check", "BTC"], [0, 1], False, "sesión wallstreet"),

    # ---- scalp-exit (reads the entry.json written above)
    ("scalp-exit plan", [EX, "plan", "--lev", "10", "--write"], [0], True, "0.25 % en contra"),
    ("scalp-exit time stop", [EX, "show"], [0], True, "afuera a las 15:02 UTC (20 minutos como máximo)"),
    ("scalp-exit hold 30 3R", [EX, "plan", "--target", "3R", "--hold", "30"], [0], True, "15:12 UTC (30 minutos"),
    ("scalp-exit atr", [EX, "plan", "--stop", "atr:2", "--offline", BTC2D], [0], True, "ATR"),
    ("scalp-exit stop too tight", [EX, "plan", "--stop", "pct:0.1"], [1], True, "under 0.15"),
    ("scalp-exit liquidation", [EX, "plan", "--stop", "pct:1", "--lev", "100"], [1], True,
     "comes before the stop"),
    ("scalp-exit utc plan", [EX, "plan", "--symbol", "BTC", "--side", "sell", "--entry", "75000", "--entry-time",
                             "02:10", "--date", "2026-11-06", "--session", "utc", "--open", "02:00", "--write",
                             "trader/plan_utc.json"], [0], True, "sesión utc"),
    ("scalp-exit utc needs open", [EX, "plan", "--symbol", "BTC", "--side", "sell", "--entry", "75000",
                                   "--entry-time", "02:10", "--date", "2026-11-06", "--session", "utc"], [1], True,
     "needs its start"),
    ("scalp-exit far plan", [EX, "plan", "--symbol", "BTC", "--side", "buy", "--entry", "74000", "--entry-time",
                             "14:42", "--date", "2026-11-06", "--write", "trader/plan_far.json"], [0], True,
     "entrada  74000"),

    # ---- scalp-timemachine (fixed seed, 28 saved days)
    ("scalp-timemachine plan", [TM, "run", "--offline", BTC28, "--now", "2026-11-06 16:40", "--write"], [0], True,
     "10,000 replays from the entry to the time stop, 14:42 UTC to 15:02 UTC (20 one-minute candles)"),
    ("scalp-timemachine flags", [TM, "run"] + BTC_LONG, [0], True, "History: the same rule (5-min opening range"),
    ("scalp-timemachine chart", [TM, "chart", "--from"], [0], True, "toward"),
    ("scalp-timemachine short 15:05", [TM, "run", "--symbol", "BTC", "--date", "2026-11-06", "--side", "sell",
                                       "--entry", "74982.9", "--stop", "75170", "--target", "74608",
                                       "--entry-time", "15:05", "--offline", BTC28, "--now", "2026-11-06 16:40"],
     [0], True, "15:05 UTC to 15:25 UTC"),
    ("scalp-timemachine europa", [TM, "run", "--session", "europa", "--symbol", "BTC", "--date", "2026-11-06",
                                  "--entry", "75589.9", "--stop", "75400", "--target", "75970", "--entry-time",
                                  "08:20", "--offline", BTC28, "--now", "2026-11-06 16:40"], [0], True,
     "europa, 08:00-10:00 UTC"),
    ("scalp-timemachine outside window", [TM, "run", "--symbol", "BTC", "--date", "2026-11-06", "--entry", "75783",
                                          "--stop", "75593", "--target", "76163", "--entry-time", "18:00",
                                          "--offline", BTC28, "--now", "2026-11-06 19:00"], [1], True,
     "inside the session window"),
    ("scalp-timemachine utc plan", [TM, "run", "--plan", "trader/plan_utc.json", "--offline", BTC28, "--now",
                                    "2026-11-06 16:40"], [0, 1], True, "02:10 UTC to 02:30 UTC"),
    ("scalp-timemachine live", [TM, "run"] + BTC_LONG[:-4], [0, 1], False, ""),

    # ---- scalp-risk (plan.json from exit; fresh journal per pass)
    ("scalp-risk pass", [RK, "check", "--capital", "3000", "--now", "2026-11-06 14:43"], [0], True, "PASA"),
    ("scalp-risk stale signal", [RK, "check", "--capital", "3000", "--now", "2026-11-06 14:50"], [1], True,
     "ya es vieja"),
    ("scalp-risk leverage", [RK, "check", "--capital", "3000", "--lev", "20", "--now", "2026-11-06 14:43"], [1],
     True, "apalancamiento 20x, el límite es 10x"),
    ("scalp-risk risk 1 %", [RK, "check", "--capital", "3000", "--risk", "1", "--now", "2026-11-06 14:43"], [1],
     True, "el límite es 0.50 %"),
    ("scalp-risk log 1", [RK, "log", "--symbol", "BTC", "--result", "-15", "--now", "2026-11-06 14:56"], [0], True, ""),
    ("scalp-risk log 2", [RK, "log", "--symbol", "ETH", "--result", "-15", "--now", "2026-11-06 15:20"], [0], True, ""),
    ("scalp-risk log 3", [RK, "log", "--symbol", "SOL", "--result", "-15", "--now", "2026-11-06 15:40"], [0], True, ""),
    ("scalp-risk three losses", [RK, "check", "--capital", "3000", "--now", "2026-11-06 14:43"], [1], True,
     "el día terminó"),
    ("scalp-risk config", [RK, "config"], [0], True, "max_signal_age_min"),

    # ---- scalp-market paper (the plan above, on the saved candles)
    ("scalp-market paper stop", [MK + "paper.py", "--capital", "3000", "--offline", BTC2D], [0], True,
     "STOP en 75593: -15.00 USD"),
    ("scalp-market paper cancelled", [MK + "paper.py", "--capital", "3000", "--plan", "trader/plan_far.json",
                                      "--offline", BTC2D], [0], True, "CANCELADA"),
    ("scalp-market paper no plan", [MK + "paper.py", "--capital", "3000", "--plan", "nope.json"], [1], True,
     "run /scalp-exit"),

    # ---- scalp-scanner (live: the universe changes)
    ("scalp-scanner universe live", [SC, "universe"], [0], False, "criptos con más de 1000 M USD"),
    ("scalp-scanner orb live", [SC, "orb", "--at", "16:30", "--symbols", "BTC,ETH,SOL"], [0, 1], False,
     "RUPTURAS DE 1 MINUTO"),
    ("scalp-scanner bad minutes", [SC, "orb", "--or-minutes", "0", "--now", "2026-11-06 16:30"], [1], True,
     "between 1 and 60"),
    ("scalp-scanner too early", [SC, "orb", "--now", "2026-11-06 14:33"], [1], True, "Run it after that"),

    # ---- scalp-social-info (the news part is the same as crypto-social-info)
    ("social patterns", [SO, "patterns"], [0], True, "malas noticias (-)"),
    ("social study politico", [SO, "study", "--scope", "politico"], [0], True, "Trump gana la elección"),
    ("social study type", [SO, "study", "--type", "prohibicion"], [0], True, "China declara ilegales"),
    ("social calendar", [SO, "calendar", "--days", "70"], [0], True, "Inflación (CPI) de noviembre"),
    ("social verify 5 confiables", [SO, "verify", "--claim", "c1", "--first-seen", "2026-11-04 06:00",
                                    "--source", "Reuters|u|confirma", "--source", "CNBC|u|confirma",
                                    "--source", "NPR|u|confirma", "--source", "Bloomberg|u|confirma",
                                    "--source", "Axios|u|confirma"], [0], True, "VERIFICADA  (#1)"),
    ("social verify oficial", [SO, "verify", "--claim", "c2", "--official", "SEC|u|confirma"], [0], True,
     "documento oficial"),
    ("social verify desmentido", [SO, "verify", "--claim", "c3", "--official", "SEC|u|desmiente",
                                  "--source", "CNN|u|confirma"], [1], True, "FALSA"),
    ("social verify X y copias", [SO, "verify", "--claim", "c4", "--social", "SECGov|u|confirma|gris",
                                  "--social", "CryptoWhale|u|confirma|azul", "--source", "Reuters|u|confirma",
                                  "--source", "Forbes|u|confirma|copia de Reuters", "--source", "CNBC|u|confirma",
                                  "--source", "NPR|u|confirma"], [1], True, "confirman 3 y hacen falta 4"),
    ("social verify X descarta azul", [SO, "verify", "--claim", "c5", "--social", "Fulano|u|confirma|azul",
                                       "--source", "CNN|u|confirma"], [1], True, "tilde azul (se compra)"),
    ("social verify medios cripto no cuentan", [SO, "verify", "--claim", "c6", "--source", "CoinDesk|u|confirma",
                                                "--source", "Cointelegraph|u|confirma", "--source",
                                                "Decrypt|u|confirma", "--source", "The Block|u|confirma",
                                                "--source", "CNBC|u|confirma"], [1], True,
     "fuera de la lista de confiables"),
    ("social verify vocero y economista", [SO, "verify", "--claim", "c7", "--vocero",
                                           "Karoline Leavitt, vocera de la Casa Blanca|u|confirma", "--economist",
                                           "Mohamed El-Erian, Queens' College Cambridge|u|confirma", "--source",
                                           "Bloomberg|u|confirma", "--source", "CNBC|u|confirma"], [0], True,
     "4 fuentes confiables confirman"),
    ("social verify parcial", [SO, "verify", "--claim", "c8", "--source", "Reuters|u|confirma", "--source",
                               "CNN|u|parcial", "--source", "NPR|u|confirma", "--source", "Axios|u|no_dice",
                               "--source", "CNBC|u|confirma"], [1], True, "datos distintos"),
    ("social verify X sin tilde", [SO, "verify", "--claim", "c9", "--social", "Fulano|u|confirma"], [1], True,
     "needs its checkmark"),
    ("social verify vocero sin cargo", [SO, "verify", "--claim", "c10", "--vocero", "Leavitt|u|confirma"], [1], True,
     "needs name and role"),
    ("social verify por país", [SO, "verify", "--claim", "c13", "--source", "VnExpress International|u|confirma",
                                "--source", "Reuters|u|confirma", "--source", "Nikkei Asia|u|confirma",
                                "--source", "Bloomberg|u|confirma", "--source", "VNA|u|confirma"], [0], True,
     "medio estatal: voz del gobierno"),
    ("social verify proporción 67 %", [SO, "verify", "--claim", "c14", "--source", "Reuters|u|confirma",
                                       "--source", "CNN|u|confirma", "--source", "NPR|u|confirma",
                                       "--source", "Axios|u|confirma", "--source", "Dawn|u|parcial",
                                       "--source", "Kompas|u|parcial"], [1], True, "hace falta el 80 %"),
    ("social verify solo estatales", [SO, "verify", "--claim", "c15", "--source", "TASS|u|confirma",
                                      "--source", "RIA Novosti|u|confirma", "--source", "Xinhua|u|confirma",
                                      "--source", "Antara|u|confirma", "--source", "Interfax|u|confirma"],
     [1], True, "las voces oficiales no alcanzan solas"),
    ("social verify alto impacto ok", [SO, "verify", "--high-impact", "--claim", "c16",
                                       "--source", "Reuters|u|confirma", "--source", "Bloomberg|u|confirma",
                                       "--source", "Nikkei|u|confirma", "--source", "Le Monde|u|confirma",
                                       "--source", "Handelsblatt|u|confirma", "--source", "Korea Herald|u|confirma"],
     [0], True, "desde 6 país(es) y 3 región(es)"),
    ("social verify alto impacto 1 región", [SO, "verify", "--high-impact", "--claim", "c17",
                                             "--source", "CNN|u|confirma", "--source", "NPR|u|confirma",
                                             "--source", "Axios|u|confirma", "--source", "CNBC|u|confirma",
                                             "--source", "Forbes|u|confirma", "--source", "Politico|u|confirma"],
     [1], True, "2 regiones o más"),
    ("social verify vieja y reciclada", [SO, "verify", "--now", "2026-11-06 19:10", "--first-seen", "2026-11-06 18:55",
                                         "--claim", "c18", "--source", "Bloomberg|u|confirma|2026-10-29 16:00",
                                         "--source", "CNBC|u|confirma|2026-10-30", "--source", "NPR|u|confirma|2026-10-31",
                                         "--source", "NBC News|u|confirma|2026-11-02",
                                         "--source", "CBS News|u|confirma|2022-10-07"], [0], True,
     "fecha: VIEJA (RECICLADA)"),
    ("social verify otro hecho no cuenta", [SO, "verify", "--now", "2026-11-06 19:10", "--claim", "c19",
                                            "--source", "Bloomberg|u|confirma|2026-11-06 12:00",
                                            "--source", "CNBC|u|confirma|2026-11-06 12:30",
                                            "--source", "NPR|u|confirma|2026-11-06 13:00",
                                            "--source", "NBC News|u|confirma|2022-10-07"], [1], True,
     "otro hecho: fecha distinta"),
    ("social verify nueva", [SO, "verify", "--now", "2026-11-06 19:10", "--claim", "c20",
                             "--source", "Reuters|u|confirma|2026-11-06 15:00", "--source", "CNBC|u|confirma|2026-11-06 15:20",
                             "--source", "NPR|u|confirma|2026-11-06 16:00", "--source", "Bloomberg|u|confirma|2026-11-06 15:05"],
     [0], True, "Es verdad y es de hoy"),
    ("social verify reciente", [SO, "verify", "--now", "2026-11-06 19:10", "--claim", "c21",
                                "--source", "Reuters|u|confirma|2026-11-05 12:00", "--source", "CNBC|u|confirma|2026-11-05",
                                "--source", "NPR|u|confirma|2026-11-05 14:00", "--source", "Bloomberg|u|confirma|2026-11-05"],
     [0], True, "buena parte ya está en el precio"),
    ("social verify recién salida por fecha", [SO, "verify", "--now", "2026-11-06 19:10", "--claim", "c22",
                                               "--source", "Reuters|u|confirma|2026-11-06 18:40",
                                               "--source", "CNBC|u|confirma|2026-11-06 18:45",
                                               "--source", "NPR|u|confirma|2026-11-06 18:50",
                                               "--source", "Bloomberg|u|confirma|2026-11-06 18:42"], [1], True,
     "salió hace 30 minutos"),
    ("social verify sin fecha", [SO, "verify", "--claim", "c23", "--source", "Reuters|u|confirma", "--source",
                                 "CNBC|u|confirma", "--source", "NPR|u|confirma", "--source", "Bloomberg|u|confirma"],
     [0], True, "falta la fecha"),
    ("social verify mismo medio", [SO, "verify", "--now", "2026-11-06 19:10", "--claim", "c24",
                                   "--source", "CNBC|u1|confirma|2026-11-06 12:00", "--source", "CNBC|u2|confirma|2026-11-06 13:00",
                                   "--source", "NPR|u|confirma|2026-11-06 12:00", "--source", "Bloomberg|u|confirma|2026-11-06 12:00"],
     [1], True, "cada medio cuenta una sola vez"),
    ("social verify fecha mala", [SO, "verify", "--claim", "c25", "--source", "Reuters|u|confirma|ayer"], [1], True,
     "YYYY-MM-DD"),
    ("social verify fecha futura", [SO, "verify", "--now", "2026-11-06 19:10", "--claim", "c26",
                                    "--source", "Reuters|u|confirma|2026-11-09"], [1], True, "in the future"),
    ("social verify blockchain y 2 diarios", [SO, "verify", "--claim", "c27", "--chain-offline", CH, "--onchain",
                                              "btc|" + PIZZA + "|10000", "--source", "CNBC|u|confirma|2010-05-22",
                                              "--source", "Forbes|u|confirma|2010-05-23"], [0], True,
     "la transacción está en la blockchain y 2 diarios"),
    ("social verify blockchain otra cifra", [SO, "verify", "--claim", "c28", "--chain-offline", CH, "--onchain",
                                             "btc|" + PIZZA + "|4259", "--source", "CNBC|u|confirma",
                                             "--source", "Forbes|u|confirma"], [1], True, "la noticia dice 4 259 BTC"),
    ("social verify blockchain no existe", [SO, "verify", "--claim", "c29", "--chain-offline", CH, "--onchain",
                                            "btc|" + "1" * 64, "--source", "CNBC|u|confirma"], [1], True,
     "no existe en la blockchain"),
    ("social verify blockchain sola", [SO, "verify", "--claim", "c30", "--chain-offline", CH, "--onchain",
                                       "btc|" + PIZZA], [1], True, "pero no de quién es"),
    ("social verify blockchain usdt", [SO, "verify", "--now", "2026-11-06 21:00", "--claim", "c31", "--chain-offline",
                                       CH, "--onchain", "eth|" + ETHTX + "|503.9 USDT", "--source",
                                       "CNBC|u|confirma|2026-11-06 19:30"], [1], True, "movió 503.91 USDT"),
    ("social verify blockchain mal id", [SO, "verify", "--claim", "c32", "--onchain", "btc|abc"], [1], True,
     "64 hex characters"),
    ("social verify blockchain coma", [SO, "verify", "--claim", "c33", "--onchain", "eth|0x" + "a" * 64 + "|4,259"],
     [1], True, "without thousands separators"),
    ("social verify blockchain en vivo", [SO, "verify", "--claim", "c34", "--onchain", "btc|" + PIZZA + "|10000",
                                          "--source", "CNBC|u|confirma|2010-05-22", "--source",
                                          "Forbes|u|confirma|2010-05-23"], [0], False, "bloque 57043"),
    ("social verify anónimas", [SO, "verify", "--now", "2026-11-06 19:10", "--claim", "c35",
                                "--source", "Bloomberg|u|confirma|2026-11-06 12:00|anonima",
                                "--source", "CNBC|u|confirma|2026-11-06 12:30|anonima",
                                "--source", "NPR|u|confirma|2026-11-06 13:00|anónima",
                                "--source", "Reuters|u|confirma|2026-11-06 13:00",
                                "--source", "CNN|u|confirma|2026-11-06 13:10"], [1], True,
     "todas juntas cuentan como una"),
    ("social verify ya en el precio", [SO, "verify", "--now", "2026-11-06 15:06", "--claim", "c36", "--coin", "BTC",
                                       "--prices", BTC2D, "--dir", "-"] + FOUR, [0], True,
     "precio: YA ESTÁ EN EL PRECIO"),
    ("social verify precio al revés", [SO, "verify", "--now", "2026-11-06 15:06", "--claim", "c37", "--coin", "BTC",
                                       "--prices", BTC2D, "--dir", "+"] + FOUR, [0], True,
     "no operes a favor de ella"),
    ("social verify precio sin fecha", [SO, "verify", "--claim", "c38", "--dir", "-", "--source", "CNN|u|confirma"],
     [1], True, "sin la fecha de la primera nota"),
    ("social verify precio en vivo", [SO, "verify", "--claim", "c39", "--dir", "+", "--first-seen",
                                      "2026-11-06 16:00", "--source", "CNN|u|confirma"], [1], False, "precio ("),
    ("social verify dir mala", [SO, "verify", "--claim", "c40", "--dir", "x", "--source", "CNN|u|confirma"], [1], True,
     "--dir is +"),
    ("social chain offline", [SO, "chain", "--offline", D + "/chainnow", "--now",
                              "2026-11-06 19:30"], [0], True, "Movimientos de 1 000 BTC o más en los últimos 6 bloques: 6"),
    ("social chain sin datos", [SO, "chain", "--offline", "/nonexistent", "--now", "2026-11-06 19:30"], [1], True, "no saved answer"),
    ("social chain en vivo", [SO, "chain"], [0], False, "Comisiones: rápida"),
    ("social verify bad stance", [SO, "verify", "--claim", "c11", "--source", "CNN|u|quizas"], [1], True,
     "the stance must be"),
    ("social verify no sources", [SO, "verify", "--claim", "c12"], [1], True, "give the sources"),
    ("social add-event refused", [SO, "--events", "ev.json", "add-event", "--date", "2026-11-04", "--country", "X",
                                  "--scope", "politico", "--type", "t", "--dir", "-", "--title", "t",
                                  "--verification", "3"], [1], True, "not VERIFICADA"),
    ("social add-event ok", [SO, "--events", "ev.json", "add-event", "--date", "2026-11-04", "--country", "EE.UU.",
                             "--scope", "politico", "--type", "elecciones", "--dir", "-", "--title", "prueba",
                             "--verification", "1"], [0], True, "Ahora hay 37 eventos"),
    ("social add-event duplicate", [SO, "--events", "ev.json", "add-event", "--date", "2026-11-04", "--country",
                                    "EE.UU.", "--scope", "politico", "--type", "elecciones", "--dir", "-",
                                    "--title", "prueba", "--verification", "1"], [1], True, "already there"),

    ("social news offline", [SO, "news", "--offline", D + "/The_Guardian.xml", "--now",
                             "2026-11-06 13:00"], [0], True, "Bitcoin slides as Democrats take Congress"),
    ("social news filtra viejas y otras", [SO, "news", "--offline", D + "/The_Guardian.xml",
                                           "--now", "2026-11-06 13:00", "--query", "stablecoin,football"],
     [0], True, "Football results"),
    ("social news for-verify", [SO, "news", "--offline", D + "/The_Guardian.xml", "--now",
                                "2026-11-06 13:00", "--query", "bitcoin", "--for-verify"], [0], True,
     '|confirma|2026-11-05 18:00"'),
    ("social news xml roto", [SO, "news", "--offline", D + "/BBC.xml"], [1], True,
     "not RSS"),
    ("social news live", [SO, "news"], [0, 1], False, "NOTICIAS de los últimos"),

    # ---- scalp-alerts
    ("scalp-alerts now live", [AL, "now", "--symbol", "BTC,ETH"], [0], False, "BTC-USD"),
]

UNIT = r'''
import importlib.util, json
sp = importlib.util.spec_from_file_location("al", "%s"); al = importlib.util.module_from_spec(sp); sp.loader.exec_module(al)
def st(side="sell", entry=2349.1, stop=2372.3, target=2302.7):
    return {"symbol": "ETH-USD", "price": [{"dir": "below", "level": 2300, "fired": False}],
            "plan": al.plan_alerts({"symbol": "ETH-USD", "side": side, "entry": entry, "stop": stop, "target": target})}
out = {}
s = st(); out["fill then target"] = al.step(s, [(0,2340,2330,2335),(60,2350,2340,2345),(120,2346,2320,2325),(180,2330,2299,2301)])
s = st(); out["missed fill"] = al.step(s, [(0,2340,2330,2335),(60,2345,2300,2302)])
s = st(); out["fill then stop"] = al.step(s, [(0,2350,2345,2348),(60,2375,2350,2370)])
s = st("buy", 100, 98, 104); out["long same-bar"] = al.step(s, [(0,101,99.9,100.5),(60,100.5,97.5,98)])
print(json.dumps(out, ensure_ascii=False, indent=1))
''' % AL


def norm(text):
    """Drop what legitimately changes between passes: wall-clock stamps."""
    return re.sub(r'"created_at": "[^"]*"', '"created_at": X', text)


def one_pass(out, only, offline_only=False):
    if os.path.exists(out):
        shutil.rmtree(out)
    work = os.path.join(out, "work")
    os.makedirs(work)
    shutil.copy(REPO + "/scalp-social-info/events.json", os.path.join(work, "ev.json"))
    results = []
    for name, args, ok_codes, det, must in CASES:
        if only and not any(name.startswith(p) for p in only):
            continue
        if offline_only and not det:
            continue
        t0 = time.time()
        p = subprocess.run([sys.executable, "-I"] + args, cwd=work, capture_output=True, text=True, timeout=900)
        text = p.stdout + p.stderr
        problems = []
        if p.returncode not in ok_codes:
            problems.append("exit %d, expected %s" % (p.returncode, ok_codes))
        if "Traceback" in text:
            problems.append("traceback")
        if must and must not in text:
            problems.append("missing %r" % must)
        results.append({"name": name, "exit": p.returncode, "det": det, "ok": not problems, "problems": problems,
                        "secs": round(time.time() - t0, 1), "out": norm(text)})
        print("%-4s %-40s %5.1fs %s" % ("ok" if not problems else "FAIL", name, time.time() - t0,
                                       "; ".join(problems)), flush=True)
    if not only or any("scalp-alerts".startswith(p) or p.startswith("scalp-alerts") for p in only):
        u = subprocess.run([sys.executable, "-I", "-c", UNIT], capture_output=True, text=True)
        results.append({"name": "scalp-alerts unit", "exit": u.returncode, "det": True, "ok": u.returncode == 0,
                        "problems": [] if u.returncode == 0 else ["unit failed"], "secs": 0,
                        "out": u.stdout + u.stderr})
        print("%-4s %-40s" % ("ok" if u.returncode == 0 else "FAIL", "scalp-alerts unit"), flush=True)
    json.dump(results, open(os.path.join(out, "results.json"), "w"), ensure_ascii=False, indent=1)
    bad = [r for r in results if not r["ok"]]
    print("\n%d casos, %d bien, %d con problemas" % (len(results), len(results) - len(bad), len(bad)), flush=True)
    return results


def main():
    ap = argparse.ArgumentParser(description="Run every command of the scalping skills.")
    ap.add_argument("--out", help="folder for the results (default: a temporary one)")
    ap.add_argument("--only", help="comma list of case-name prefixes, e.g. scalp-entry,social")
    ap.add_argument("--twice", action="store_true", help="run two passes and compare the offline cases")
    ap.add_argument("--offline-only", action="store_true", help="skip the cases that read live prices")
    a = ap.parse_args()
    out = a.out or tempfile.mkdtemp(prefix="scalp-tests-")
    only = [x.strip() for x in a.only.split(",")] if a.only else None
    first = one_pass(os.path.join(out, "pass1"), only, a.offline_only)
    ok = all(r["ok"] for r in first)
    if a.twice:
        print("\n--- segunda pasada ---")
        second = one_pass(os.path.join(out, "pass2"), only, a.offline_only)
        ok = ok and all(r["ok"] for r in second)
        diffs = [x["name"] for x, y in zip(first, second) if x["det"] and x["out"] != y["out"]]
        print("Casos sin red que dieron distinto entre pasadas: %s" % (", ".join(diffs) or "ninguno"))
        ok = ok and not diffs
    print("Resultados en %s" % out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
