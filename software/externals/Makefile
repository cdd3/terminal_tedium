CC ?= cc
PD_INCLUDE ?= /usr/include/pd
CFLAGS ?= -O2 -g
WARN = -Wall -Wextra -Wno-cast-function-type -Wno-unused-parameter
BUILD = build
NAMES = terminal_tedium_adc tedium_input tedium_output tedium_switch
ALL = $(addprefix $(BUILD)/,$(addsuffix .pd_linux,$(NAMES)))
.PHONY: all clean check
all: $(ALL) $(BUILD)/tt_gpio_inspect
$(BUILD)/tt_gpio_inspect: tt_gpio_inspect.c | $(BUILD)
	$(CC) $(CFLAGS) $(WARN) -std=c99 -o $@ $<
$(BUILD):
	mkdir -p $@
$(BUILD)/libtt_gpio.so: tt_gpio.c tt_gpio.h | $(BUILD)
	$(CC) $(CFLAGS) $(WARN) -std=c99 -fPIC -shared -Wl,-soname,libtt_gpio.so -o $@ tt_gpio.c
$(BUILD)/terminal_tedium_adc.pd_linux: terminal_tedium_adc.c | $(BUILD)
	$(CC) $(CFLAGS) $(WARN) -std=c99 -D_GNU_SOURCE -fPIC -shared -I$(PD_INCLUDE) -o $@ $< -lm
$(BUILD)/tedium_%.pd_linux: tedium_%.c tt_gpio.h $(BUILD)/libtt_gpio.so
	$(CC) $(CFLAGS) $(WARN) -std=c99 -fPIC -shared -I$(PD_INCLUDE) -o $@ $< -L$(BUILD) -ltt_gpio -Wl,-rpath,'$$ORIGIN' -lm
check: $(BUILD)/test_gpio
	$(BUILD)/test_gpio
$(BUILD)/test_gpio: tests/test_gpio.c tt_gpio.c tt_gpio.h | $(BUILD)
	$(CC) $(CFLAGS) $(WARN) -std=c99 -I. -o $@ tests/test_gpio.c
clean:
	$(RM) -r $(BUILD)

