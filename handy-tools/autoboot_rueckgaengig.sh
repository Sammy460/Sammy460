#!/system/bin/sh
# Spielt das Backup zurueck.  su -c sh /sdcard/phonedeck/autoboot_rueckgaengig.sh
BOOT=$(ls /dev/block/by-name/boot /dev/block/platform/*/by-name/boot \
       /dev/block/platform/*/*/by-name/boot 2>/dev/null | head -n 1)
dd if=/sdcard/phonedeck/boot_backup.img of="$BOOT" && echo "Backup zurueckgespielt."
