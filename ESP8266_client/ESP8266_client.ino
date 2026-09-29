/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *
 *  This is the main sketch file.
 *  It provides a periodic pooling of other services.
 */

#include "HardwareSerial.h"
#include "config.h"
#include "http_client.h"
#include "http_server.h"
#include "ui.h"
#include "wifi_connection.h"

static String statusMessage =
    ""; /* This is set and requested from other modules. */

void MAIN_setStatusMsg(String msg) { statusMessage = msg; }

String MAIN_getStatusMsg(void) { return statusMessage; }

void setup(void) {
  /* Need to wait for background processes to complete. Otherwise trouble with
   * gpio.*/
  delay(100);
  Serial.begin(115200);
  UI_init();
  WIFIC_init();
  HTTP_SERVER_init();
}

void loop(void) {
  if (WIFIC_isApMode()) {
    HTTP_SERVER_process();
  }
  HTTP_CLIENT_process(); /* Does nothing until STA is connected */

  WIFIC_process();
  UI_process();
}
