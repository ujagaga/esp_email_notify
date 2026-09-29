#ifndef HTTP_CLIENT_H
#define HTTP_CLIENT_H

#include <Arduino.h>

extern void HTTP_CLIENT_process(void);
extern bool HTTP_CLIENT_send(String id, String text);

#endif
