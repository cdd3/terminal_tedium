/*
 *  left outlet: print time
 *  right outlet: print 1 when pushed, 0 when released
 *
 */

#include <m_pd.h>
#include <stdio.h>
#include "tt_gpio.h"
#include <errno.h>
#include <string.h>

t_class *tedium_switch_class;

typedef struct _tedium_switch
{
	t_object x_obj;
	t_clock *x_clock;
	t_int clkState;
	t_int switchState;
	t_int ticks;
	t_int pinNum;
    int gpio_owned;
    int gpio_failed;
	t_outlet *x_out1;
	t_outlet *x_out2;

} t_tedium_switch;

void tedium_switch_tick(t_tedium_switch *x)
{
	int prevState = x->clkState;
	if (!x->gpio_owned || x->gpio_failed) return;
    int value = tt_gpio_read(x->pinNum);
    if (value < 0) {
        pd_error(x, "GPIO %d read failed: %s", (int)x->pinNum, strerror(errno));
        x->gpio_failed = 1;
        return;
    }
    x->clkState = value;
	// pin pulled low since last tick ?
	if(prevState && !x->clkState) {
		x->switchState = 0x1;
		outlet_float(x->x_out2, 0x1);
	}
	// released ? 
	if (!prevState && x->clkState) {
		outlet_float(x->x_out1, x->ticks);
		outlet_float(x->x_out2, 0x0);
		x->switchState = 0x0;
		x->ticks = 0x0;
	}
	// delay 1 msec
	clock_delay(x->x_clock, 0x1);
	// if button is held, count++
	if (x->switchState == 0x1) {
		x->ticks++;
	}
}

void *tedium_switch_new(t_floatarg _pin)
{
	t_tedium_switch *x = (t_tedium_switch *)pd_new(tedium_switch_class);
	x->x_clock = clock_new(x, (t_method)tedium_switch_tick);
	// valid pin?
	if (_pin == 23 || _pin == 24 || _pin == 25) x->pinNum = _pin;
	else x->pinNum = 23; // default to pin #23
	// init 
	x->clkState = 1;
	x->switchState = 0;
	x->ticks = 0;
	x->gpio_owned = (tt_gpio_acquire(x->pinNum, 0) == 0);
    x->gpio_failed = 0;
    if (!x->gpio_owned) pd_error(x, "GPIO %d acquire failed (set TT_GPIO_CHIP): %s", (int)x->pinNum, strerror(errno));
    x->clkState = 1;
	x->x_out1 = outlet_new(&x->x_obj, gensym("float"));
	x->x_out2 = outlet_new(&x->x_obj, gensym("float"));
	tedium_switch_tick(x);
	return (void *)x;
}

void tedium_switch_free(t_tedium_switch *x)
{
	clock_free(x->x_clock);
    if (x->gpio_owned) tt_gpio_release(x->pinNum);
	outlet_free(x->x_out1);
	outlet_free(x->x_out2); 
}

void tedium_switch_setup()
{
		
	tedium_switch_class = class_new(gensym("tedium_switch"),
		(t_newmethod)tedium_switch_new, (t_method)tedium_switch_free,
		sizeof(t_tedium_switch), 
		CLASS_NOINLET, 
		A_DEFFLOAT,
		0);
}

