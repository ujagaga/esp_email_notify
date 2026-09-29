/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *
 *  Finds the server on the local network, polls it for new mail and sends
 *  the selected response.
 */
#include "config.h"
#include "ui.h"
#include <ArduinoJson.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#define MAX_RESPONSES 8

static unsigned long lastConnectAtemptTime = 0;
static String serverUrl = ""; /* Empty until discovered */

/* Broadcast "email_check?" and wait for "email_check:<port>" from the server */
static void discoverServer(void) {
  WiFiUDP udp;
  udp.begin(DISCOVERY_PORT);
  udp.beginPacket(IPAddress(255, 255, 255, 255), DISCOVERY_PORT);
  udp.print("email_check?");
  udp.endPacket();

  unsigned long start = millis();
  while ((millis() - start) < 1000) {
    if (udp.parsePacket() > 0) {
      String reply = udp.readString();
      if (reply.startsWith("email_check:")) {
        serverUrl = "http://" + udp.remoteIP().toString() + ":" + reply.substring(12);
        Serial.println("Server found: " + serverUrl);
        break;
      }
    }
    delay(10);
  }
  udp.stop();
}

static void checkMail(void) {
  WiFiClient client;
  HTTPClient http;
  http.begin(client, serverUrl + "/check");
  http.addHeader("X-Api-Key", DEVICE_KEY);
  int httpCode = http.GET();

  if (httpCode <= 0) {
    Serial.printf("HTTP GET failed, error: %s\n", http.errorToString(httpCode).c_str());
    serverUrl = ""; /* Server may have moved, look for it again */
    UI_showText("Server lost");
    http.end();
    return;
  }

  String response = http.getString();
  http.end();
  Serial.print("HTTP RX:");
  Serial.println(response);

  JsonDocument doc;
  if (deserializeJson(doc, response) != DeserializationError::Ok) {
    return;
  }

  String responses[MAX_RESPONSES];
  int count = 0;
  for (JsonVariant r : doc["responses"].as<JsonArray>()) {
    if (count < MAX_RESPONSES) {
      responses[count++] = r.as<String>();
    }
  }

  UI_setMail(doc["id"] | "", doc["message"] | "", responses, count);
  if (doc["beep"] | false) {
    UI_beep();
  }
}

static String urlEncode(String text) {
  String encoded = "";
  for (char c : text) {
    if (isalnum(c) || (c == '-') || (c == '_') || (c == '.') || (c == '~')) {
      encoded += c;
    } else {
      char hex[4];
      snprintf(hex, sizeof(hex), "%%%02X", (uint8_t)c);
      encoded += hex;
    }
  }
  return encoded;
}

bool HTTP_CLIENT_send(String id, String text) {
  if (serverUrl.length() == 0) {
    return false;
  }

  WiFiClient client;
  HTTPClient http;
  http.begin(client, serverUrl + "/send");
  http.addHeader("X-Api-Key", DEVICE_KEY);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  int httpCode = http.POST("id=" + id + "&text=" + urlEncode(text));
  http.end();

  lastConnectAtemptTime = 0; /* Check again right away */
  return httpCode == 200;
}

void HTTP_CLIENT_process() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  if (((millis() - lastConnectAtemptTime) > (UPDATE_TIMEOUT + random(100))) ||
      (lastConnectAtemptTime == 0)) {
    if (serverUrl.length() == 0) {
      UI_showText("Looking for\nserver...");
      discoverServer();
    }
    if (serverUrl.length() > 0) {
      checkMail();
    }
    lastConnectAtemptTime = millis();
  }
}
