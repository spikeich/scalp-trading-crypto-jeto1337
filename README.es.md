# Scalp trading crypto · jeto1337

[English](README.md) · **Español**

Ocho skills de Claude para practicar **scalping de cripto con velas de 1
minuto**: primero las noticias y la blockchain, después las criptos que rompen
sus primeros 5 minutos en la apertura de Londres o de Wall Street, el momento
de entrar, un stop chico y una salida por tiempo, el tamaño según tu riesgo con
hasta 10x aislado, 10.000 repeticiones del scalp y la simulación en papel con
las comisiones de Binance.

**Leé esto primero: en nuestras pruebas, el scalping perdió plata después de
comisiones.** Cuatro semanas de velas de 1 minuto, 480 configuraciones, y
ninguna ganó en las dos mitades de la muestra. Estas skills son un simulador
para practicar y medir con honestidad, no una máquina de ganar. Mirá
[Lo que mostraron los datos](#lo-que-mostraron-los-datos).

Gratis, MIT, sin registro, sin API key. Python con la biblioteca estándar.
**Nada de esto opera por vos**: ninguna skill manda órdenes a una exchange.

El repo hermano, de day trading con velas de 5 minutos:
[skill-cryptos-jeto1337](https://github.com/spikeich/skill-cryptos-jeto1337).
Se pueden instalar los dos juntos: estas skills se llaman `scalp-*`.

## Instalación

En Claude Code, como plugin:

```
/plugin marketplace add spikeich/scalp-trading-crypto-jeto1337
/plugin install scalp-trading-crypto-jeto1337@scalp-trading-crypto-jeto1337
```

O copiando las carpetas:

```bash
git clone https://github.com/spikeich/scalp-trading-crypto-jeto1337.git
cp -r scalp-trading-crypto-jeto1337/scalp-* ~/.claude/skills/
```

Necesitan Python 3.8+ y salida a `query1.finance.yahoo.com`,
`query2.finance.yahoo.com` y `api.coingecko.com`, más `mempool.space` y
`eth.blockscout.com` para la blockchain y `www.theguardian.com`,
`rss.nytimes.com` y `feeds.bbci.co.uk` para las noticias.

## Las ocho skills

| comando | qué hace |
| --- | --- |
| `/scalp-social-info` | **Primero, siempre.** Noticias verificadas con 5 fuentes confiables y con fecha, prueba de transacciones en la blockchain, el estado de las redes de Bitcoin y Ethereum, y el calendario: nada de scalps nuevos desde 15 minutos antes hasta 15 minutos después de un evento. |
| `/scalp-scanner` | **Qué está rompiendo.** Solo las criptos más líquidas (más de 1.000 M USD por día) que rompen los primeros 5 minutos de Londres o de Wall Street con 2 cierres de 1 minuto seguidos. |
| `/scalp-entry` | **Cuándo entrar.** Vela por vela, el momento en que 2 cierres de 1 minuto seguidos quedan afuera del rango o de un nivel. Las entradas vencen 2 horas después de la apertura. |
| `/scalp-exit` | **Dónde salir.** Stop de 0,25 %, objetivo 2R y salida a los 20 minutos por defecto, con el R neto de comisiones y la liquidación para tu apalancamiento. |
| `/scalp-timemachine` | **¿Tiene ventaja?** 10.000 repeticiones de los 20 minutos siguientes con las velas de 1 minuto de esa cripto en las últimas 4 semanas, y la misma regla en cada día pasado. |
| `/scalp-risk` | **¿Entra en tus límites?** 0,5 % de riesgo por operación, hasta 10x aislado, R neto de al menos 1,2, un scalp a la vez, 3 pérdidas y se termina el día, una señal de más de 3 minutos ya es vieja. Imprime la orden para cargar a mano en Binance. |
| `/scalp-alerts` | **Mientras está abierto.** Entrada llenada, stop, objetivo, una orden límite que no se llenó, hora de salir, con el máximo y el mínimo de la última vela de 1 minuto cada 20 segundos. |
| `/scalp-market` | **Tamaño y simulación.** El tamaño según tu riesgo (no según el apalancamiento) y la simulación del plan sobre velas reales de 1 minuto, con comisiones, en USD. |

## Cómo se usan juntas

```
/scalp-social-info  noticias, blockchain, calendario: ¿es momento de scalpear?
/scalp-scanner      qué rompió los primeros 5 minutos
/scalp-entry        la vela exacta para entrar        -> trader/entry.json
/scalp-exit         stop, objetivo, salida por tiempo -> trader/plan.json
/scalp-timemachine  ¿ese plan tiene ventaja?
/scalp-risk         ¿entra en mis límites? cuánto, y la orden para Binance
/scalp-alerts       lo vigila mientras está abierto
/scalp-market       lo simula en papel con comisiones
```

## El apalancamiento, sin vueltas

El apalancamiento no cambia lo que perdés: lo marca el stop. Con 3.000 USD,
0,5 % de riesgo y un stop de 0,25 %, la posición es de unos 6.000 USD y el stop
cuesta 15 USD a 5x, 10x o 20x. El apalancamiento solo decide cuánto margen
queda trabado y dónde queda la liquidación:

| apalancamiento | margen trabado | liquidación | si salta el stop |
| --- | --- | --- | --- |
| 5x | 1.200 USD | a ~19 % | -15 USD |
| 10x | 600 USD | a ~9,5 % | -15 USD |
| 20x | 300 USD | a ~4,5 % | -15 USD |
| 50x | 120 USD | a ~1,5 % | -15 USD |

La trampa es usarlo para agrandar la posición. `/scalp-risk` lo limita a 10x y
rechaza un plan con la liquidación a menos del doble de distancia que el stop.

## Lo que mostraron los datos

`research/bt.py`: 4 semanas de velas de 1 minuto (del 10 de octubre al 5 de
noviembre de 2026) de BTC, ETH, SOL, XRP y DOGE, aperturas de Londres y Nueva
York, de lunes a viernes, entradas en las 2 primeras horas. 480
configuraciones: rangos de apertura de 5 y 15 minutos, mini rangos de 15
minutos, operar al revés de las rupturas falsas, de 1 a 3 velas de
confirmación, stops de 0,15 a 0,35 % o en el otro extremo del rango, objetivos
de 1,5R a 3R, salida a los 15 o 30 minutos, entrada a mercado o con orden
límite. Cada una se eligió con las primeras dos semanas y se juzgó con las
últimas dos.

| | sin comisiones | con comisiones de Binance |
| --- | --- | --- |
| promedio por operación, semanas 1-2 | +0,08 R | **−0,27 R** |
| promedio por operación, semanas 3-4 | −0,03 R | **−0,39 R** |
| configuraciones que ganaron en las dos mitades | 96 de 480 | **0 de 480** |

- **Las comisiones se comen todo.** Con stop de 0,25 %, la ida y vuelta de
  Binance cuesta unos 0,3 R por operación. Sin comisiones quedaban cerca del
  empate; con comisiones no sobrevivió ninguna.
- **La mejor de la primera mitad perdió en la segunda.** Ganó +24 R en las
  semanas 1-2 y perdió −29 R en las 3-4: suerte, no ventaja.
- **Las órdenes límite ayudan, pero no alcanza.** Pierden un poco menos.

Cuatro semanas es una muestra corta, y las velas de Yahoo no son el libro de
órdenes de Binance (sin spread ni fila). Igual la dirección es clara: el
scalping minorista pelea primero contra las comisiones y después contra el
mercado.

Para repetirlo:

```bash
cd research
python3 fetch1m.py BTC-USD ETH-USD SOL-USD XRP-USD DOGE-USD
python3 bt.py
python3 bt.py --no-fees
```

## Sesiones

| sesión | abre | UTC (invierno del norte) | Argentina | ventana de scalping |
| --- | --- | --- | --- | --- |
| `europa` | 08:00 Londres | 08:00 | 05:00 | las 2 primeras horas |
| `wallstreet` | 09:30 Nueva York | 14:30 | 11:30 | las 2 primeras horas |

Cada día se calcula con sus propios horarios de verano.

## Tests

`python3 tests/run_all.py --twice` corre todos los comandos, los que usan datos
guardados dos veces, y revisa que las dos pasadas den lo mismo. Los que leen
en vivo necesitan la red.

## Créditos

Hecho a partir de [skill-cryptos-jeto1337](https://github.com/spikeich/skill-cryptos-jeto1337),
cuyas skills de escáner, entrada, salida, máquina del tiempo, riesgo y alertas
son adaptaciones a cripto de las skills `trader-*` de
[Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill)
(MIT). Su aviso de copyright está en `LICENSE-day-trader-skill`.

## Aviso

Esto es análisis de datos y un simulador, no un consejo de inversión. Operar
con apalancamiento puede hacerte perder todo lo que pusiste, y en nuestras
pruebas el scalping perdió después de comisiones. Practicá primero en el modo
demo de tu exchange.
