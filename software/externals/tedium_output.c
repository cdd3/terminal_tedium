/***********************************************************************
 * terminal tedium: GPIO
 * outputs: 
 * pcm5102a version: GPIO 16, 26 
 * wm8731   version: GPIO 12, 16
 * ****************************************************************************/


#include <m_pd.h>
#include <stdio.h>
#include "tt_gpio.h"
#include <errno.h>
#include <string.h>

t_class *tedium_output_class;

typedef struct _tedium_output
{
	t_object x_obj;
	t_int clkState;
	t_int pinNum;
    int gpio_owned;
    int gpio_failed;

} t_tedium_output;

void tedium_output_gate(t_tedium_output *x, t_floatarg _gate)
{
	if (_gate > 0)	x->clkState = 1; 
	else		x->clkState = 0;
	if (x->gpio_owned && !x->gpio_failed && tt_gpio_write(x->pinNum, x->clkState) < 0) {
        pd_error(x, "GPIO %d write failed: %s", (int)x->pinNum, strerror(errno));
        x->gpio_failed = 1;
    }
}

void *tedium_output_new(t_floatarg _pin)
{
	t_tedium_output *x = (t_tedium_output *)pd_new(tedium_output_class);

	// valid pin?
	if (_pin == 12 || _pin == 16 || _pin == 26) x->pinNum = _pin;
	else x->pinNum = 16; // default to pin #16
	x->gpio_owned = (tt_gpio_acquire(x->pinNum, 1) == 0);
    x->gpio_failed = 0;
    if (!x->gpio_owned) pd_error(x, "GPIO %d acquire failed (set TT_GPIO_CHIP): %s", (int)x->pinNum, strerror(errno));
	x->clkState = 0;
	return (void *)x;
}



void tedium_output_free(t_tedium_output *x)
{
    if (x->gpio_owned) tt_gpio_release(x->pinNum);
}

void tedium_output_setup()
{
		
	tedium_output_class = class_new(gensym("tedium_output"),
		(t_newmethod)tedium_output_new,
		(t_method)tedium_output_free, sizeof(t_tedium_output), 
		CLASS_DEFAULT, 
		A_DEFFLOAT,
		0);
	class_addfloat(tedium_output_class, (t_method)tedium_output_gate);
}

