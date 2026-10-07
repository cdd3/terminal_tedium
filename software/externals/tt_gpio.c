#define _GNU_SOURCE
#include "tt_gpio.h"
#include <linux/gpio.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct line { int fd; unsigned refs; int output; };
static struct line lines[54];

int tt_gpio_acquire(unsigned pin, int output)
{
    if (pin >= 54) { errno = EINVAL; return -1; }
    struct line *l = &lines[pin];
    if (l->refs) {
        if (l->output != output) { errno = EBUSY; return -1; }
        l->refs++;
        return 0;
    }
    const char *path = getenv("TT_GPIO_CHIP");
    if (!path || !*path) { errno = ENODEV; return -1; }
    int chip = open(path, O_RDONLY | O_CLOEXEC);
    if (chip < 0) return -1;
    struct gpiochip_info info = {0};
    if (ioctl(chip, GPIO_GET_CHIPINFO_IOCTL, &info) < 0) {
        int e = errno; close(chip); errno = e; return -1;
    }
    /* Initial scope: BCM2835 pin controller on Pi 3B+. Reject expander chips. */
    if (strcmp(info.label, "pinctrl-bcm2835") || pin >= info.lines) {
        close(chip); errno = ENODEV; return -1;
    }
    struct gpio_v2_line_request request = {0};
    request.offsets[0] = pin;
    request.num_lines = 1;
    snprintf(request.consumer, sizeof(request.consumer), "terminal-tedium");
    request.config.flags = output ? GPIO_V2_LINE_FLAG_OUTPUT :
        GPIO_V2_LINE_FLAG_INPUT | GPIO_V2_LINE_FLAG_BIAS_PULL_UP;
    if (output) {
        request.config.num_attrs = 1;
        request.config.attrs[0].attr.id = GPIO_V2_LINE_ATTR_ID_OUTPUT_VALUES;
        request.config.attrs[0].attr.values = 0;
        request.config.attrs[0].mask = 1;
    }
    int result = ioctl(chip, GPIO_V2_GET_LINE_IOCTL, &request);
    int e = errno;
    close(chip);
    if (result < 0) { errno = e; return -1; }
    l->fd = request.fd; l->refs = 1; l->output = output;
    return 0;
}

int tt_gpio_read(unsigned pin)
{
    if (pin >= 54 || !lines[pin].refs || lines[pin].output) {
        errno = EINVAL; return -1;
    }
    struct gpio_v2_line_values v = { .mask = 1 };
    if (ioctl(lines[pin].fd, GPIO_V2_LINE_GET_VALUES_IOCTL, &v) < 0)
        return -1;
    return !!(v.bits & 1);
}

int tt_gpio_write(unsigned pin, int value)
{
    if (pin >= 54 || !lines[pin].refs || !lines[pin].output) {
        errno = EINVAL; return -1;
    }
    struct gpio_v2_line_values v = { .mask = 1, .bits = !!value };
    return ioctl(lines[pin].fd, GPIO_V2_LINE_SET_VALUES_IOCTL, &v);
}

void tt_gpio_release(unsigned pin)
{
    if (pin >= 54 || !lines[pin].refs) return;
    struct line *l = &lines[pin];
    if (--l->refs) return;
    if (l->output) {
        struct gpio_v2_line_values v = { .mask = 1, .bits = 0 };
        (void)ioctl(l->fd, GPIO_V2_LINE_SET_VALUES_IOCTL, &v);
    }
    close(l->fd);
    memset(l, 0, sizeof(*l));
}

