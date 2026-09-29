# ESP Email Notify

A small standalone gadget that checks a mailbox for **unread emails from specific
senders** and alerts you with a message on an old Nokia 5110 LCD and a few beeps
from a piezo speaker.

## Hardware

- ESP8266 D1 mini
- Nokia 5110 LCD module (PCD8544 controller, 84x48 pixels)
- Piezo speaker (passive buzzer)
- 2x push button
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

| Push button | D1 mini pin | GPIO   | Notes                                |
|-------------|-------------|--------|----------------------------------------|
| Button 1    | D3          | GPIO0  | Other leg to GND, use internal pull-up |
| Button 2    | D4          | GPIO2  | Other leg to GND, use internal pull-up |

Don't hold either button pressed while the board powers up or resets: GPIO0
low selects flash mode and GPIO2 must be high at boot.

Free pins for later use: D0, RX, TX, A0.

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

  Push buttons (other leg of each to GND, internal pull-up)
  Button 1 ---- D3 (D1 mini)
  Button 2 ---- D4 (D1 mini)
```

## Setup

1. `tools/install_dependencies.sh`
2. Copy `config.h.example` to `config.h` and set `DEVICE_KEY` to the server's
   `DEVICE_KEY` (see `PythonServer/config.py`).
3. Build and flash: `tools/build.sh`, `tools/upload_usb.sh`
4. On first start, connect to the WiFi AP shown on the LCD
   (`AP_NAME` from `config.h`, password `PASSWORD`), open `http://192.168.4.1`
   and save your network. The device restarts and joins it.

After every start the setup AP stays up for `AP_MODE_TIMEOUT_S` (5 min) in
AP+STA mode. After that the device switches to STA only once no one is
connected to the AP.

## Behaviour

- Finds the server by broadcasting `email_check?` to UDP `DISCOVERY_PORT`, and
  looks again if the server stops answering.
- Polls the server's `/check` every `UPDATE_TIMEOUT` ms and shows the result on
  the LCD. New mail plays a short 3-tone beep.
- **Button 1 (D3)** cycles through the server's responses, shown inverted at
  the bottom of the LCD.
- **Button 2 (D4)** sends the selected response as a reply to the shown mail,
  which is then marked read.
