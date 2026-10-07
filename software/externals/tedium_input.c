/* NB: pullups need to be set for the inputs to work */


#include <m_pd.h>
#include <stdio.h>
#include "tt_gpio.h"
#include <errno.h>
#include <string.h>

t_class *tedium_input_class;

typedef struct _tedium_input
{
	t_object x_obj;
	t_clock *x_clock;
	t_int clkState;
	t_int pinNum;
    int gpio_owned;
    int gpio_failed;
	t_outlet *x_out;

} t_tedium_input;

void tedium_input_tick(t_tedium_input *x)
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
	if(prevState && !x->clkState) outlet_bang(x->x_out);
	clock_delay(x->x_clock, 0x1); 
}

void *tedium_input_new(t_floatarg _pin)
{
	t_tedium_input *x = (t_tedium_input *)pd_new(tedium_input_class);
	x->x_clock = clock_new(x, (t_method)tedium_input_tick);
	// valid pin?
	if (_pin == 4 || _pin == 17 || _pin == 2 || _pin == 3 || _pin == 14 || _pin == 27 || _pin == 23 || _pin == 24 || _pin == 25) x->pinNum = _pin;
	else x->pinNum = 4; // default to pin #4	
	x->gpio_owned = (tt_gpio_acquire(x->pinNum, 0) == 0);
    x->gpio_failed = 0;
    if (!x->gpio_owned) pd_error(x, "GPIO %d acquire failed (set TT_GPIO_CHIP): %s", (int)x->pinNum, strerror(errno));
    x->clkState = 1;
	x->x_out = outlet_new(&x->x_obj, gensym("bang"));
	tedium_input_tick(x);
	return (void *)x;
}

void tedium_input_free(t_tedium_input *x)
{
	clock_free(x->x_clock);
    if (x->gpio_owned) tt_gpio_release(x->pinNum);
	outlet_free(x->x_out);  
}

void tedium_input_setup()
{
		
	tedium_input_class = class_new(gensym("tedium_input"),
		(t_newmethod)tedium_input_new, (t_method)tedium_input_free,
		sizeof(t_tedium_input), 
		CLASS_NOINLET, 
		A_DEFFLOAT,
		0);
}

