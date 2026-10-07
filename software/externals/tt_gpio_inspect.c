#include <linux/gpio.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr,"usage: %s /dev/gpiochipN\n",argv[0]); return 2; }
    int fd=open(argv[1],O_RDONLY);
    if(fd<0) { perror("open"); return 1; }
    struct gpiochip_info i={0};
    if(ioctl(fd,GPIO_GET_CHIPINFO_IOCTL,&i)<0) { perror("chip info"); close(fd); return 1; }
    printf("%s: name=%s label=%s lines=%u\n",argv[1],i.name,i.label,i.lines);
    close(fd); return 0;
}

