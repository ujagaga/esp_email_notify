#ifndef UI_H
#define UI_H

#include <Arduino.h>

extern void UI_init(void);
extern void UI_process(void);
extern void UI_showText(String text);
extern void UI_setMail(String id, String message, String *responses, int count);
extern void UI_beep(void);

#endif
