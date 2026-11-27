#!/system/bin/sh
# Auto-Boot beim Einstecken fuer Redmi 9A (und andere Magisk-Geraete).
# Baut eine Regel in das (schon mit Magisk gepatchte) Boot-Image ein.
# Ausfuehren als root:  su -c sh /sdcard/phonedeck/autoboot_einrichten.sh
set -e
DIR=/sdcard/phonedeck
WORK=/data/local/tmp/autoboot
MB=/data/adb/magisk/magiskboot

[ "$(id -u)" = "0" ] || { echo "Bitte mit su starten"; exit 1; }
[ -x "$MB" ] || { echo "magiskboot fehlt - ist Magisk installiert?"; exit 1; }

BOOT=$(ls /dev/block/by-name/boot /dev/block/platform/*/by-name/boot \
       /dev/block/platform/*/*/by-name/boot 2>/dev/null | head -n 1)
[ -n "$BOOT" ] || { echo "Boot-Partition nicht gefunden"; exit 1; }
echo "Boot-Partition: $BOOT"

rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"
dd if="$BOOT" of=boot.img
cp boot.img "$DIR/boot_backup.img"
echo "Backup: $DIR/boot_backup.img  (auf den PC kopieren!)"

"$MB" unpack boot.img
[ -f ramdisk.cpio ] || { echo "Kein ramdisk.cpio - Abbruch, nichts geaendert"; exit 1; }
"$MB" cpio ramdisk.cpio "mkdir 0750 overlay.d" \
  "add 0644 overlay.d/autoboot.rc $DIR/autoboot.rc"
"$MB" repack boot.img new-boot.img

dd if=new-boot.img of="$BOOT"
echo "Fertig. Test: Handy ausschalten, Kabel einstecken -> sollte booten."
