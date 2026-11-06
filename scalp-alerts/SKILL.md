---
name: scalp-alerts
description: >-
  Alertas para scalping de cripto: sigue el plan de /scalp-exit minuto a
  minuto y avisa cuando el precio llega a la entrada, toca el stop o el
  objetivo, la orden nunca se llenó, o se cumple la salida por tiempo. También
  alertas de precio sueltas. Nunca toca órdenes. Usala cuando el usuario diga
  "vigilá el scalp", "avisame si toca el stop del scalp", "a cuánto está BTC",
  o mientras un scalp está abierto.
---

# scalp-alerts

Adaptación de `crypto-alerts` (repo skill-cryptos-jeto1337), que viene de
`trader-alerts` de [Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill)
(MIT, ver `LICENSE-day-trader-skill`).

```bash
python3 "${CLAUDE_SKILL_DIR}/alerts.py" watch                       # trader/plan.json
python3 "${CLAUDE_SKILL_DIR}/alerts.py" watch --symbol BTC --above 76000 --below 75000 --plan none
python3 "${CLAUDE_SKILL_DIR}/alerts.py" now --symbol BTC,ETH
```

Mira cada 20 segundos (`--every`) la última vela de 1 minuto cerrada, con su
máximo y su mínimo, así una mecha entre dos miradas igual cuenta. Imprime una
línea cuando arranca, una por alerta y un "sigue vigilando" cada 5 minutos
(`--heartbeat`). Termina cuando el scalp terminó (stop, objetivo, orden que no
se llenó o salida por tiempo) o a la hora (`--max-hours`). Corrélo bajo
`Monitor` y avisale al usuario solo lo que importa.

| evento | qué quiere decir |
| --- | --- |
| ENTRADA | el precio llegó a la entrada: una orden límite ahí se llenaba |
| STOP / OBJETIVO | tocado después de la entrada: el scalp terminó |
| PERDIDA | llegó al stop o al objetivo sin pasar por la entrada: la orden no se llenó, cancelala |
| HORA DE SALIR | la salida por tiempo del plan: afuera, gane o pierda |

Yahoo puede ir uno o dos minutos atrás de Binance: en scalping eso es mucho.
Para operar de verdad, mirá el precio en la app de la exchange.
