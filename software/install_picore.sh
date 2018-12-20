#!/bin/sh

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
#tce-load -iw wireless_tools
#tce-load -iw wpa_supplicant
tce-load -iw firmware-rpi3-wireless
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
git clone https://github.com/cdd3/tt_patches
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

if [[ "$HARDWARE_VERSION" == 'armv6l' ]]; then
	cp $HOME/terminal_tedium/software/rt_start_armv6 $HOME/terminal_tedium/software/rt_start
else
	cp $HOME/terminal_tedium/software/rt_start_armv7 $HOME/terminal_tedium/software/rt_start
fi

sudo chmod +x $HOME/terminal_tedium/software/rt_start

sudo echo "$HOME/terminal_tedium/software/rt_start" >> /opt/bootlocal.sh

cp $HOME/terminal_tedium/software/pdpd $HOME/startpd.sh
sudo chmod +x $HOME/startpd.sh  

sudo echo "$HOME/startpd.sh" >> /opt/bootlocal.sh  # run startup script for pd on boot

#echo ""
#echo ""

echo "boot/config ... ---------------------------------------------------------"

mount /dev/mmcblk0p1

sudo cp /mnt/mmcblk0p1/config.txt /mnt/mmcblk0p1/config.txt.old #backup original config.txt
sudo chmod -w /mnt/mmcblk0p1/config.txt.old
sudo cp $HOME/terminal_tedium/software/config_picore.txt /mnt/mmcblk0p1/config.txt

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

sudo echo "/etc/asound.conf" >> /opt/.filetool.lst
sudo echo '/usr/local/lib/pd/extra' >> /opt/.filetool.lst

filetool.sh -b

echo ""
echo ""
echo ""
echo ""

echo " edit startpd.sh to point to the patch you want to load at startup.  
when done type "sudo reboot" to restart system"
#sudo reboot
echo ""
