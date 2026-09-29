/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *
 *  Nokia 5110 LCD, piezo speaker and the two buttons.
 *  Button 1 cycles through the responses, button 2 sends the selected one.
 */
#include "config.h"
#include "http_client.h"
#include "ui.h"
#include <Adafruit_PCD8544.h>

#define LCD_DC_PIN 4   // D2
#define LCD_CS_PIN 15  // D8
#define LCD_RST_PIN 5  // D1
#define SPEAKER_PIN 12 // D6
#define BTN_SELECT_PIN 0 // D3
#define BTN_OK_PIN 2     // D4
#define MAX_RESPONSES 8
#define DEBOUNCE_MS 50

static Adafruit_PCD8544 display(LCD_DC_PIN, LCD_CS_PIN, LCD_RST_PIN);
static String mailId = "";
static String mailMessage = "";
static String responses[MAX_RESPONSES];
static int responseCount = 0;
static int selected = -1; /* -1: no response selected */

static void draw(void) {
  display.clearDisplay();
  display.setTextColor(BLACK);
  display.setCursor(0, 0);
  display.print(mailMessage);

  if (selected >= 0) {
    /* Bottom two text lines show the selected response, inverted */
    display.fillRect(0, 32, LCDWIDTH, 16, BLACK);
    display.setTextColor(WHITE);
    display.setCursor(0, 32);
    display.print(responses[selected]);
  }
  display.display();
}

/* Returns true once per press */
static bool buttonPressed(uint8_t pin, bool &down, unsigned long &changedAt) {
  bool now = digitalRead(pin) == LOW;
  if ((now == down) || ((millis() - changedAt) < DEBOUNCE_MS)) {
    return false;
  }
  down = now;
  changedAt = millis();
  return down;
}

void UI_init(void) {
  pinMode(BTN_SELECT_PIN, INPUT_PULLUP);
  pinMode(BTN_OK_PIN, INPUT_PULLUP);
  display.begin(LCD_CONTRAST);
  UI_showText("Starting...");
}

void UI_showText(String text) {
  mailMessage = text;
  mailId = "";
  responseCount = 0;
  selected = -1;
  draw();
}

void UI_setMail(String id, String message, String *newResponses, int count) {
  responseCount = min(count, MAX_RESPONSES);
  for (int i = 0; i < responseCount; i++) {
    responses[i] = newResponses[i];
  }

  if ((id == mailId) && (message == mailMessage) && (selected < responseCount)) {
    return; /* Nothing changed, keep the current selection */
  }
  mailId = id;
  mailMessage = message;
  selected = -1;
  draw();
}

void UI_beep(void) {
  const int tones[] = {1000, 1500, 2000};
  for (int f : tones) {
    tone(SPEAKER_PIN, f, 100);
    delay(130);
  }
}

void UI_process(void) {
  static bool selectDown = false, okDown = false;
  static unsigned long selectChangedAt = 0, okChangedAt = 0;

  if (buttonPressed(BTN_SELECT_PIN, selectDown, selectChangedAt) && (responseCount > 0)) {
    selected = (selected + 1) % responseCount;
    draw();
  }

  if (buttonPressed(BTN_OK_PIN, okDown, okChangedAt) && (selected >= 0)) {
    String id = mailId;
    String text = responses[selected];
    UI_showText("Sending...");
    UI_showText(HTTP_CLIENT_send(id, text) ? "Sent" : "Send failed");
  }
}
