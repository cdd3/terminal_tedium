#!/bin/sh

# This is a setup / install script for the terminal tedium eurorack module by mxmxmx
# it is a modified version of his install script and should be considered a work in progress
# it will configure a picore linux system to starup puredata from a usb drive
# more info on the usb drive setup on github
# this has only been tested on a pi 3 model b attached to a wm8731 version of the TT using picore 9.0.3

echo ""
echo ""
echo ""
echo ">>>>> terminal tedium <<<<<< --------------------------------------------"
echo ""
echo "(sit back, this will take a 2-3 minutes)"
echo ""

PD_VERSION="pd-0.47-1"

HARDWARE_VERSION=$(uname -m)

if [[ "$HARDWARE_VERSION" == 'armv6l' ]]; then
		echo "--> using armv6l (A+, zero)"
elif [[ "$HARDWARE_VERSION" == 'armv7l' ]]; then
		echo "--> using armv7l (pi2, pi3)"
else
	echo "not using pi ?... exiting"
	exit -1
fi
echo ""
echo "installing required packages ... ----------------------------------------"
echo ""
#tce-load -iw git
tce-load -iw make
tce-load -iw gcc
tce-load -iw compiletc
tce-load -iw wget
tce-load -iw tar
tce-load -iw acl
tce-load -iw wiringpi
tce-load -iw wiringpi-dev
tce-load -iw libunistring
tce-load -iw alsa
tce-load -iw alsa-utils
tce-load -iw puredata
#tce-load -iw wifi

echo ""

echo "copy terminal tedium externals... ---------------------------------------"
#echo ""
#cd $HOME 
#rm -r -f $HOME/terminal_tedium >/dev/null 2>&1
#git clone https://github.com/cdd3/terminal_tedium
#cd $HOME/terminal_tedium
#git pull origin

sudo cp $HOME/terminal_tedium/software/externals/*.pd_linux /usr/local/lib/pd/extra

echo ""


echo "clone terminal tedium patches... ---------------------------------------"
echo ""
cd $HOME 
rm -r -f $HOME/tt_patches >/dev/null 2>&1
#git clone https://github.com/cdd3/tt_patches
#cd $HOME/terminal_tedium
#git pull origin


echo ""


#echo " > abl_link~"
#cd $HOME/terminal_tedium/software/externals/abl_link/
#sudo mv abl_link~.pd_linux $HOME/$PD_VERSION/extra/

#echo ""

echo "done installing software... ---------------------------------------------"

echo ""
echo ""

echo "configuring startup scripts... ------------------------------------------"
echo ""

sudo echo "mount /dev/sda1" >> /opt/bootlocal.sh  # mount the usb stick 

if [[ "$HARDWARE_VERSION" == 'armv6l' ]]; then
	cp $HOME/terminal_tedium/software/rt_start_armv6 $HOME/terminal_tedium/software/rt_start
else
	cp $HOME/terminal_tedium/software/rt_start_armv7 $HOME/terminal_tedium/software/rt_start
fi

sudo chmod +x $HOME/terminal_tedium/software/rt_start

sudo echo "$HOME/terminal_tedium/software/rt_start" >> /opt/bootlocal.sh

cp $HOME/terminal_tedium/software/pdpd_usb.sh $HOME/startpd.sh
sudo chmod +x $HOME/startpd.sh  

sudo echo "$HOME/startpd.sh" >> /opt/bootlocal.sh  # run startup script for pd on boot

#echo ""
#echo ""

echo "boot/config ... ---------------------------------------------------------"

mount /dev/mmcblk0p1

sudo cp /mnt/mmcblk0p1/config.txt /mnt/mmcblk0p1/config.txt.old #backup original config.txt
sudo chmod 440 /mnt/mmcblk0p1/config.txt.bak	#make backup read-only (still doesn't work, don't know why yet maybe vfat?)
sudo cp $HOME/terminal_tedium/software/config_picore.txt /mnt/mmcblk0p1/config.txt

# apperantely the shell won't let you pipe straight to root owned files (even with sudo) so write a tmp file
#add startup delay for slow usb drives
sudo cp /mnt/mmcblk0p1/cmdline3.txt /mnt/mmcblk0p1/cmdline3.txt.bak
awk '//{$10="waitusb=10"}{print}' /mnt/mmcblk0p1/cmdline3.txt > cmdline3.tmp
sudo mv cmdline3.tmp /mnt/mmcblk0p1/cmdline3.txt

# change sda1 to automatically mout at startup
awk '/\/dev\/sda1/{$4="auto,users,exec,umask=000"}{print}' /etc/fstab > fstab.tmp	
sudo mv fstab.tmp /etc/fstab

echo ""
echo ""

echo "alsa ... ----------------------------------------------------------------"

sudo cp $HOME/terminal_tedium/software/asound.conf /etc/asound.conf

echo ""
echo ""

echo "done ... cleaning up ----------------------------------------------------"

# remove hardware files and other stuff that's not needed
#cd $HOME/terminal_tedium/software/
#rm -r externals
#rm asound.conf
#rm pdpd
#rm pullup.py
#rm rc.local
#rm rt_start_armv*
#rm config.txt
#rm install.sh
#cd $HOME/terminal_tedium/
#rm -rf hardware
#rm *.md
#cd $HOME
#rm install.sh

echo "Saving System State  ----------------------------------------------------"

sudo echo '/etc/fstab' >> /opt/.filetool.lst
sudo echo '/etc/asound.conf' >> /opt/.filetool.lst
sudo echo '/usr/local/lib/pd/extra' >> /opt/.filetool.lst

#filetool.sh -b

echo ""
echo ""
echo ""
echo ""

echo " edit startpd.sh to point to the patch you want to load at startup.  
when done type "sudo reboot" to restart system"
#sudo reboot
echo ""
