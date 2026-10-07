#!/usr/bin/env bash
# ============================================================
# export-drivers.sh — каталогизация драйверов Windows-раздела из Linux
#
# Парная версия export-drivers.ps1. DISM в Linux недоступен, поэтому скрипт
# монтирует Windows-раздел ТОЛЬКО ДЛЯ ЧТЕНИЯ и каталогизирует Driver Store
# с построением манифеста SHA256. Это копия, а не выгрузка: для получения
# установленных INF-пакетов в пригодном для /Add-Driver виде нужен DISM из
# WinPE (export-drivers.ps1 -WinImage).
#
# Запуск:
#   sudo bash export-drivers.sh --device /dev/nvme0n1p3 --destination /mnt/tools/backup/drivers
#   sudo bash export-drivers.sh --device /dev/nvme0n1p3 --destination /mnt/x --dry-run
#
# Коды возврата: 0 — успех, 1 — ошибка, 2 — нет прав или утилит, 3 — устройство/каталог недоступны.
# ============================================================
set -uo pipefail

DEVICE='' DEST='' MOUNTPOINT='' DRYRUN=0 UNMOUNT=0

usage() { sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -d|--device)      DEVICE="${2:?}"; shift 2 ;;
        -D|--destination) DEST="${2:?}";   shift 2 ;;
        -m|--mountpoint)  MOUNTPOINT="${2:?}"; UNMOUNT=1; shift 2 ;;
        --dry-run)        DRYRUN=1; shift ;;
        -h|--help)        usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

die()  { echo "ОШИБКА: $*" >&2; exit "${2:-1}"; }
log()  { echo "$*"; }
run()  { if [ "$DRYRUN" -eq 1 ]; then echo "  [dry-run] $*"; else eval "$@"; fi; }

[ -n "$DEVICE" ] && [ -n "$DEST" ] || { echo 'Нужны --device и --destination' >&2; usage 1; }
[ "$(id -u)" -eq 0 ] || die 'требуются права root' 2
command -v sha256sum >/dev/null 2>&1 || die 'нет sha256sum' 2
[ -b "$DEVICE" ] || die "$DEVICE не является блочным устройством" 3

DRIVER_STORE='Windows/System32/DriverStore/FileRepository'

if [ -z "$MOUNTPOINT" ]; then
    MOUNTPOINT="$(mktemp -d /tmp/winmount.XXXXXX)"
    UNMOUNT=1
fi

log "Устройство:   $DEVICE"
log "Точка монтирования: $MOUNTPOINT"
log "Назначение:  $DEST"

run "mkdir -p '$MOUNTPOINT' '$DEST'"

if [ "$DRYRUN" -eq 0 ]; then
    mount -o ro "$DEVICE" "$MOUNTPOINT" || die "не удалось смонтировать $DEVICE только для чтения" 3
    trap '[ "$UNMOUNT" -eq 1 ] && umount "$MOUNTPOINT" 2>/dev/null; rmdir "$MOUNTPOINT" 2>/dev/null || true' EXIT
fi

SRC="$MOUNTPOINT/$DRIVER_STORE"
if [ "$DRYRUN" -eq 0 ] && [ ! -d "$SRC" ]; then
    die "в $DEVICE не найден $DRIVER_STORE — это не системный раздел Windows?" 3
fi

log "Каталогизирую $DRIVER_STORE ..."
run "cp -a '$SRC/.' '$DEST/'"

COUNT=0
if [ "$DRYRUN" -eq 0 ]; then
    COUNT=$(find "$DEST" -type f | wc -l | tr -d ' ')
    MANIFEST="$DEST/manifest.sha256.csv"
    {
        echo 'path,sha256,size_bytes,modified,captured_at'
        STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
        find "$DEST" -type f ! -name 'manifest.sha256.csv' -print0 |
        while IFS= read -r -d '' f; do
            rel="${f#"$DEST"/}"
            h="$(sha256sum "$f" | awk '{print $1}')"
            sz="$(stat -c%s "$f")"
            mt="$(date -r "$f" '+%Y-%m-%d %H:%M:%S')"
            echo "$rel,$h,$sz,$mt,$STAMP"
        done
    } > "$MANIFEST"
    log "Файлов скопировано: $COUNT"
    log "Манифест: $MANIFEST"
else
    log "  [dry-run] манифест SHA256 будет построен в $DEST/manifest.sha256.csv"
fi

log ''
log 'Внимание: это КОПИЯ Driver Store. Для получения пакетов, пригодных для'
log 'DISM /Add-Driver, выполните из WinPE: export-drivers.ps1 -WinImage C:\'
exit 0
