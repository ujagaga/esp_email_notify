# ESP Email Notify

A small standalone gadget that checks a mailbox for **unread emails from specific
senders** and alerts you with a message on an old Nokia 5110 LCD and a few beeps
from a piezo speaker.

## Hardware

- ESP8266 D1 mini
- Nokia 5110 LCD module (PCD8544 controller, 84x48 pixels)
- Piezo speaker (passive buzzer)
- Breadboard + jumper wires
- 330 Ω resistor (LCD backlight, optional)

## Wiring

| Nokia 5110 pin | D1 mini pin | GPIO    | Notes                          |
|-----------------|-------------|---------|---------------------------------|
| VCC             | 3V3         | -       | Module is 3.3V only, do not use 5V |
| GND             | G           | -       |                                  |
| SCLK            | D5          | GPIO14  | Hardware SPI clock (SCK)        |
| DIN (MOSI)      | D7          | GPIO13  | Hardware SPI data (MOSI)        |
| D/C             | D2          | GPIO4   | Data/command select             |
| RST             | D1          | GPIO5   | Reset                           |
| CE (CS)         | D8          | GPIO15  | Hardware SPI chip select        |
| BL (backlight)  | 3V3         | -       | Through 330 Ω resistor, or GND if it's active-low on your module |

| Piezo speaker | D1 mini pin | GPIO   | Notes            |
|---------------|-------------|--------|-------------------|
| +             | D6          | GPIO12 |                   |
| -             | G           | -      |                   |

Free pins for later use: D0, D3, D4, RX, TX, A0.

## Schematic

```
  Nokia 5110 LCD                          Piezo speaker
  ,-------------.                         ,--------.
  | VCC  --------- 3V3 (D1 mini)          | +  ---- D6 (D1 mini)
  | GND  --------- GND (D1 mini)          | -  ---- GND (D1 mini)
  | SCLK --------- D5  (D1 mini)          `--------'
  | DIN  --------- D7  (D1 mini)
  | D/C  --------- D2  (D1 mini)
  | RST  --------- D1  (D1 mini)
  | CE   --------- D8  (D1 mini)
  | BL   --------- 3V3 (D1 mini, via 330R)
  `-------------'
```

## Planned behaviour

- Periodically poll the mailbox for unread messages.
- Filter unread messages to a configured list of sender addresses.
- On a match, show the sender/subject on the Nokia 5110 LCD.
- Sound a short beep pattern on the piezo speaker.

Firmware details (mail provider/API, polling interval, config options) will be
added once the hardware is wired up and tested.
