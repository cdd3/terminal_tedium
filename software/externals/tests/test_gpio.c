#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
#include <linux/gpio.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
static int requests, closes, writes, read_value=1, fail_read;
static const char *label = "pinctrl-bcm2835";
static int fake_open(const char *p, int flags, ...) { (void)p; (void)flags; return 9; }
static int fake_close(int fd) { if(fd>=100) closes++; return 0; }
static int fake_ioctl(int fd, unsigned long op, ...) {
    (void)fd;
    va_list a; va_start(a,op); void *v=va_arg(a,void*); va_end(a);
    if(op==GPIO_GET_CHIPINFO_IOCTL) {
        struct gpiochip_info *i=v; strcpy(i->label,label); i->lines=54;
    } else if(op==GPIO_V2_GET_LINE_IOCTL) {
        struct gpio_v2_line_request *r=v;
        if(r->config.flags & GPIO_V2_LINE_FLAG_OUTPUT)
            assert(r->config.attrs[0].attr.values==0 && r->config.attrs[0].mask==1);
        else assert(r->config.flags & GPIO_V2_LINE_FLAG_BIAS_PULL_UP);
        r->fd=100+requests++;
    } else if(op==GPIO_V2_LINE_GET_VALUES_IOCTL) {
        if(fail_read) { errno=EIO; return -1; }
        ((struct gpio_v2_line_values*)v)->bits=read_value;
    } else if(op==GPIO_V2_LINE_SET_VALUES_IOCTL) writes++;
    else assert(0);
    return 0;
}
#define open fake_open
#define close fake_close
#define ioctl fake_ioctl
#include "../tt_gpio.c"
#undef open
#undef close
#undef ioctl
int main(void) {
    unsetenv("TT_GPIO_CHIP");
    assert(tt_gpio_acquire(23,0)==-1);
    setenv("TT_GPIO_CHIP","/dev/mock",1);
    label="raspberrypi-exp-gpio";
    assert(tt_gpio_acquire(23,0)==-1 && requests==0);
    label="pinctrl-bcm2835";
    assert(tt_gpio_acquire(23,0)==0);
    assert(tt_gpio_acquire(23,0)==0 && requests==1);
    assert(tt_gpio_acquire(23,1)==-1);
    assert(tt_gpio_read(23)==1);
    read_value=0; assert(tt_gpio_read(23)==0);
    fail_read=1; assert(tt_gpio_read(23)==-1);
    tt_gpio_release(23); assert(closes==0);
    tt_gpio_release(23); assert(closes==1);
    assert(tt_gpio_acquire(16,1)==0);
    assert(tt_gpio_write(16,1)==0);
    tt_gpio_release(16); assert(writes==2 && closes==2);
    assert(tt_gpio_acquire(54,0)==-1);
    return 0;
}

