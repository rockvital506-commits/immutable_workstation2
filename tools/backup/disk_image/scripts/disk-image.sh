#!/usr/bin/env bash
# ============================================================
# disk-image.sh — образ диска через Clonezilla + дамп таблицы разделов
#
# Запускается из Clonezilla Live. Снимает образ устройства и отдельный дамп
# MBR/GPT: без дампа восстановление таблицы разделов на другой геометрии
# становится лотереей.
#
# Запуск:
#   sudo bash disk-image.sh --device /dev/nvme0n1 --destination /home/partimg --name MSI_B12M_before
#   sudo bash disk-image.sh --device /dev/nvme0n1 --destination /home/partimg --name test --dry-run
#
# Коды возврата: 0 — успех, 1 — ошибка, 2 — нет утилит, 3 — устройство/каталог недоступны.
#
# Ограничения Clonezilla: целевой раздел >= исходного; инкрементальных образов
# нет; раздел должен быть размонтирован; из образа нельзя достать один файл.
# BitLocker-том снимается через dd размером с весь том — сначала приостановите
# шифрование.
# ============================================================
set -uo pipefail

DEVICE='' DEST='' NAME='' DRYRUN=0 COMPRESSION='-z9p'

usage() { sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -d|--device)      DEVICE="${2:?}"; shift 2 ;;
        -D|--destination) DEST="${2:?}";   shift 2 ;;
        -n|--name)        NAME="${2:?}";   shift 2 ;;
        -z|--compression) COMPRESSION="${2:?}"; shift 2 ;;
        --dry-run)        DRYRUN=1; shift ;;
        -h|--help)        usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

die() { echo "ОШИБКА: $*" >&2; exit "${2:-1}"; }
run() { if [ "$DRYRUN" -eq 1 ]; then echo "  [dry-run] $*"; else eval "$@"; fi; }

[ -n "$DEVICE" ] && [ -n "$DEST" ] && [ -n "$NAME" ] || { echo 'Нужны --device, --destination, --name' >&2; usage 1; }
[ "$(id -u)" -eq 0 ] || die 'требуются права root' 2
[ -b "$DEVICE" ] || die "$DEVICE не является блочным устройством" 3

OCS='/opt/drbl/sbin/ocs-sr'
[ -x "$OCS" ] || die "$OCS не найден — скрипт нужно запускать из Clonezilla Live" 2
command -v sgdisk >/dev/null 2>&1 || die 'нет sgdisk' 2

# Раздел устройства не должен быть смонтирован
if mount | grep -q "^$DEVICE"; then
    die "разделы $DEVICE смонтированы — Clonezilla не работает со смонтированным томом" 3
fi

# Свободное место в назначении
mkdir -p "$DEST" || die "не удалось создать $DEST" 3
AVAIL_KB=$(df -Pk "$DEST" | awk 'NR==2 {print $4}')
AVAIL_GB=$((AVAIL_KB / 1024 / 1024))
echo "Свободно в $DEST: ${AVAIL_GB} ГБ"
[ "$AVAIL_GB" -ge 20 ] || echo "ВНИМАНИЕ: мало места — образ может не поместиться"

echo "Устройство: $DEVICE"
echo "Имя образа: $NAME"

# --- 1. Дамп таблицы разделов ---
run "sgdisk --backup='$DEST/${NAME}-gpt.bak' '$DEVICE'"
run "dd if='$DEVICE' of='$DEST/${NAME}-mbr.img' bs=512 count=1 status=none"

# --- 2. Образ диска ---
# -e1 auto  : создание ФС при восстановлении
# -c        : восстановление с того же устройства
# -r        : повторные попытки при ошибках чтения
# -j2       : клонирование скрытых разделов
# -p true   : выключиться после завершения
run "$OCS -q2 -c -j2 $COMPRESSION -i 4096 -e1 auto -e2 -r -p true savedisk '$NAME' '$DEVICE'"

if [ "$DRYRUN" -eq 1 ]; then
    echo
    echo 'Ничего не изменено (--dry-run).'
    exit 0
fi

# --- 3. Манифест ---
MANIFEST="$DEST/${NAME}.manifest.sha256.csv"
{
    echo 'path,sha256,size_bytes,captured_at'
    STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
    find "$DEST" -path "$DEST/$NAME" -prune -o -type f -print |
    grep -v '\.manifest\.sha256\.csv$' |
    while IFS= read -r f; do
        echo "${f#"$DEST"/},$(sha256sum "$f" | awk '{print $1}'),$(stat -c%s "$f"),$STAMP"
    done
    find "$DEST/$NAME" -type f 2>/dev/null |
    while IFS= read -r f; do
        echo "${f#"$DEST"/},$(sha256sum "$f" | awk '{print $1}'),$(stat -c%s "$f"),$STAMP"
    done
} > "$MANIFEST"

echo "Манифест: $MANIFEST"
echo 'Готово. Для восстановления: ocs-sr ... restoredisk <имя> <устройство>'
exit 0
