/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *
 *  WiFi connection module.
 */
#include "config.h"
#include "ui.h"
#include <ESP8266WiFi.h>
#include <Preferences.h>
#include <lwip/dns.h>
#include <lwip/init.h>
#include <lwip/ip_addr.h>

static char mySsidName[32] = {0}; /* Array to form AP name based on read MAC */
static char deviceName[32] = {0};
static String st_ssid = ""; /* SSID to connect to */
static String st_pass = ""; /* Password for the requested SSID */
static unsigned long connectionTimeoutCheck = 0;
static IPAddress stationIP;
static IPAddress apIP(192, 168, 4, 1); /* Not 192.168.1.x, that is a common LAN range */
static bool apMode = false;
static uint32_t apModeAttempTime = 0;
static IPAddress dns(8, 8, 8, 8);

static bool checkValidIp(IPAddress IP) {
  /* check if they are all zero value */
  if ((IP[0] == 0) && (IP[1] == 0) && (IP[2] == 0) && (IP[3] == 0)) {
    return false;
  }

  /* Check that they are not all 0xff (defaut empty flash value) */
  if ((IP[0] == 0xff) && (IP[1] == 0xff) && (IP[2] == 0xff) &&
      (IP[3] == 0xff)) {
    return false;
  }

  return true;
}

char *WIFIC_getDeviceName(void) { return deviceName; }

IPAddress WIFIC_getApIp(void) { return apIP; }

bool WIFIC_isApMode(void) { return apMode; }

/* Returns wifi scan results */
String WIFIC_getApList(void) {
  String result = "";
  // WiFi.scanNetworks will return the number of networks found
  int n = WiFi.scanNetworks();
  if (n > 0) {
    result = WiFi.SSID(0);
    for (int i = 1; i < n; ++i) {
      result += "|" + WiFi.SSID(i);
    }
  }
  return result;
}

/* Initiates a local AP */
void WIFIC_APMode(void) {
  String wifi_statusMessage;
  Serial.println("\nStarting AP");

  WiFi.mode(WIFI_AP);
  WiFi.begin();

  String macAddr = WiFi.macAddress();
  macAddr.replace(":", "");
  macAddr.toCharArray(deviceName, sizeof(deviceName));

  String ApName = AP_NAME;
  ApName.toCharArray(mySsidName, ApName.length() + 1);

  WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0));

  if (WiFi.softAP(mySsidName, PASSWORD)) {
    wifi_statusMessage = "Running in AP mode. SSID: " + String(mySsidName) +
                         ", IP:" + apIP.toString();
    apMode = true;
    UI_showText("WiFi setup\nAP: " + String(mySsidName) + "\nPass: " + PASSWORD + "\n" + apIP.toString());
  } else {
    wifi_statusMessage = "Failed to switch to AP mode.";
  }
  Serial.println(wifi_statusMessage);

  apModeAttempTime = millis();
}

void WIFIC_stationMode(void) {
  Serial.printf("\n\nTrying STA mode with [%s] and [%s]\r\n", st_ssid.c_str(), st_pass.c_str());

  bool useStaticIp = checkValidIp(stationIP);
  if (useStaticIp) {
    IPAddress subnet(255, 255, 255, 0);
    IPAddress gateway(stationIP[0], stationIP[1], stationIP[2], 1);

    WiFi.config(stationIP, gateway, IPAddress(255, 255, 255, 0), dns);
  } else {
    WiFi.config(0U, 0U, 0U); // This disables static config.
  }

  /* Does not wait, so the setup page stays usable. The SDK keeps retrying. */
  WiFi.begin(st_ssid.c_str(), st_pass.c_str());
}

String WIFIC_getStSSID(void) { return st_ssid; }

void WIFIC_setStSSID(String new_ssid) {
  Preferences prefs;
  prefs.begin("wifi");
  prefs.putString("ssid", new_ssid);
  prefs.end();
  st_ssid = new_ssid;
}

String WIFIC_getStPass(void) { return st_pass; }

void WIFIC_setStPass(String new_pass) {
  Preferences prefs;
  prefs.begin("wifi");
  prefs.putString("pass", new_pass);
  prefs.end();
  st_pass = new_pass;
}

IPAddress WIFIC_getStIP(void) { return stationIP; }

void WIFIC_init(void) {
  ESP.wdtFeed();
  Preferences prefs;
  prefs.begin("wifi", true);
  st_ssid = prefs.getString("ssid", "");
  st_pass = prefs.getString("pass", "");
  prefs.end();

  WIFIC_APMode();
  if (st_ssid.length() > 0) {
    WIFIC_stationMode(); /* AP+STA */
  }
}

void WIFIC_process(void) {
  static unsigned long lastCheckTime = 0;
  static bool wasConnected = false;
  const unsigned long checkInterval = 5000; // 5 seconds

  bool connected = WiFi.status() == WL_CONNECTED;
  if (connected && !wasConnected) {
    stationIP = WiFi.localIP();
    IPAddress gateway = WiFi.gatewayIP();
    // force dns server
    ip_addr_t dnsserver;
    IP4_ADDR(&dnsserver, dns[0], dns[1], dns[2], dns[3]);
    dns_setserver(0, &dnsserver);

    Serial.printf("IP address: %s, gateway: %s \n",
                  stationIP.toString().c_str(), gateway.toString().c_str());
  }
  wasConnected = connected;

  if (!apMode) {
    return;
  }

  unsigned long now = millis();

  // Keep the AP for AP_MODE_TIMEOUT_S after startup, so there is time to
  // connect to it and change settings.
  if ((now - apModeAttempTime) < (AP_MODE_TIMEOUT_S * 1000)) {
    return;
  }

  if ((now - lastCheckTime) < checkInterval) {
    return;
  }
  lastCheckTime = now;

  if (!connected) {
    return;
  }

  // Already connected in AP+STA mode: drop to STA only once no client is
  // using the device's AP any more.
  if (wifi_softap_get_station_num() == 0) {
    Serial.println("No AP clients — switching to STA only.");
    WiFi.mode(WIFI_STA);
    apMode = false;
  }
}
