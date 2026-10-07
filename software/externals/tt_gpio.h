#ifndef TT_GPIO_H
#define TT_GPIO_H
/* Shared across externals through libtt_gpio.so. Pd message thread only. */
int tt_gpio_acquire(unsigned pin, int output);
void tt_gpio_release(unsigned pin);
int tt_gpio_read(unsigned pin);
int tt_gpio_write(unsigned pin, int value);
#endif

