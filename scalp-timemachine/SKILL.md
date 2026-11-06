---
name: scalp-timemachine
description: >-
  Máquina del tiempo para scalping de cripto: repite 10.000 veces los minutos
  que dura el scalp (de la entrada a la salida por tiempo) con velas reales de
  1 minuto de las últimas 4 semanas de esa cripto, y vuelve a correr la misma
  regla en cada día pasado. Dice qué tan seguido toca primero el objetivo, el
  stop, o ninguno, y da un veredicto honesto. Usala cuando el usuario diga
  "máquina del tiempo del scalp", "simulá este scalp", "qué probabilidades
  tiene el scalp", o antes de abrir un plan de /scalp-exit.
---

# scalp-timemachine

Adaptación de `crypto-timemachine` (repo skill-cryptos-jeto1337), que viene de
`trader-timemachine` de [Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill)
(MIT, ver `LICENSE-day-trader-skill`). Mismo algoritmo, con velas de 1 minuto.

```bash
python3 "${CLAUDE_SKILL_DIR}/timemachine.py" run                 # trader/plan.json, hasta su flat_by
python3 "${CLAUDE_SKILL_DIR}/timemachine.py" run --write
python3 "${CLAUDE_SKILL_DIR}/timemachine.py" run --symbol BTC --date 2026-11-06 --side buy \
    --entry 75783 --stop 75593 --target 76163 --entry-time 14:42 --hold 20
python3 "${CLAUDE_SKILL_DIR}/timemachine.py" chart
```

Otras opciones: `--session wallstreet|europa|utc` (`--window-utc`), `--until`,
`--replays`, `--seed` (19), `--window` (2 minutos), `--offline`, `--now`.
Necesita `query2.finance.yahoo.com` (4 consultas: Yahoo da 7 días de velas de
1 minuto por consulta y guarda unos 30).

## Cómo funciona

1. **El banco de velas:** unas 4 semanas de velas de 1 minuto, de la ventana
   de la sesión (las **2 primeras horas** de Wall Street o de Londres). Los
   días a los que les faltan hasta 5 minutos se completan con una vela plana
   al último cierre; los que tienen más huecos se dejan afuera.
2. **10.000 repeticiones** desde el precio de entrada hasta la **salida por
   tiempo** del plan (`flat_by`, entrada + 20 minutos): cada minuto se arma
   con una vela pasada del mismo minuto (±2), escalada al precio. Si una vela
   toca el stop y el objetivo, cuenta el stop.
3. **La historia:** la misma regla (rango de 5 minutos, 2 velas, el mismo stop
   y objetivo, afuera a los 20 minutos) en cada día pasado.
4. **El veredicto:** compara las veces que llegó primero el objetivo con lo que
   hace falta para empatar a ese R: 1 de cada (1 + R).

**Las comisiones no están en esos R:** con stop de 0,25 % cuestan ~0,3 R por
operación. Un veredicto "cerca del empate" en scalping es, en realidad,
perder.

## Lo que mostraron los datos

4 semanas de velas de 1 minuto (BTC, ETH, SOL, XRP, DOGE), aperturas de
Londres y Nueva York, de lunes a viernes, 480 configuraciones: **ninguna ganó
después de comisiones en las dos mitades de la muestra** (promedio −0,27 R y
−0,39 R por operación). Sin comisiones quedaban cerca del empate. Este repo es
un simulador para practicar y medir, no una máquina de ganar: decíselo al
usuario cada vez que lo use.

Cerrá siempre con que es una simulación con datos del pasado y no un consejo
de inversión. Siguiente: `/scalp-risk`.
