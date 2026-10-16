#!/usr/bin/env bash
# ============================================================
# bios-inventory.sh — фиксация версий прошивок платы ДО любых изменений
#
# Парная версия bios-inventory.ps1. Скрипт НИЧЕГО не прошивает: он только
# записывает то, что потом не восстановить по памяти. Обновление BIOS
# возвращает настройки UEFI к значениям по умолчанию, поэтому снимок настроек
# обязателен до, а не после.
#
# Запуск:
#   sudo bash bios-inventory.sh                      # снимок в /tmp
#   bash bios-inventory.sh --out /mnt/tools/... --dry-run
#
# Коды возврата: 0 — успех, 1 — ошибка, 2 — нет нужных утилит, 3 — каталог недоступен.
# ============================================================
set -euo pipefail

# Лог в файл (CONVENTIONS.md, раздел 5). Скрипт перезапускает сам себя через
# tee, а не через process substitution: `wait` в trap виснет, если `set -e`
# обрывает скрипт внутри функции, а tee ещё жив. Код возврата возвращается
# через PIPESTATUS, поэтому для вызывающего поведение не меняется.
LOG_FILE="${TMPDIR:-/tmp}/${0##*/}.log"
if [ -z "${_LOGGED_SELF:-}" ]; then
    _LOGGED_SELF=1 exec bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"
    exit "${PIPESTATUS[0]}"
fi
echo "=== ${0##*/} $(date '+%Y-%m-%d %H:%M:%S') ==="

OUT="${TMPDIR:-/tmp}" DRYRUN=0

usage() { sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -o|--out)     OUT="${2:?}"; shift 2 ;;
        --dry-run)    DRYRUN=1; shift ;;
        -h|--help)    usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

die() { echo "ОШИБКА: $*" >&2; exit "${2:-1}"; }
run() { if [ "$DRYRUN" -eq 1 ]; then echo "  [dry-run] $*"; else eval "$@"; fi; }

# --- Что доступно в этой среде -------------------------------------------
HAVE_DMI=0 HAVE_EFI=0 HAVE_TPM=0
command -v dmidecode >/dev/null 2>&1 && HAVE_DMI=1
[ -d /sys/firmware/efi ] && HAVE_EFI=1
if command -v tpm2_pcrread >/dev/null 2>&1 || command -v tpm2_getcap >/dev/null 2>&1; then HAVE_TPM=1; fi

echo "dmidecode: $([ "$HAVE_DMI" -eq 1 ] && echo есть || echo нет)"
echo "UEFI-режим: $([ "$HAVE_EFI" -eq 1 ] && echo да || echo нет)"
echo "tpm2-tools: $([ "$HAVE_TPM" -eq 1 ] && echo есть || echo нет)"

if [ "$HAVE_DMI" -eq 0 ] && [ "$HAVE_EFI" -eq 0 ]; then
    die "нет ни dmidecode, ни /sys/firmware/efi — снимать нечем" 2
fi

# --- Куда пишем -----------------------------------------------------------
if [ "$DRYRUN" -eq 0 ]; then
    [ -d "$OUT" ] || die "каталог недоступен: $OUT" 3
    [ -w "$OUT" ] || die "каталог не для записи: $OUT" 3
fi
STAMP="$(date '+%Y%m%d-%H%M%S')"
REPORT="$OUT/bios-inventory-$STAMP.txt"
echo "Отчёт: $REPORT"

# --- Снимок ---------------------------------------------------------------
{
    echo "# Снимок прошивок и настроек UEFI"
    echo "# Дата: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# Снято до изменений. После прошивки сверить с этим файлом."
    echo

    echo "## Плата и BIOS"
    if [ "$HAVE_DMI" -eq 1 ]; then
        dmidecode -t system 2>/dev/null | grep -E 'Manufacturer|Product Name|Version|Serial' \
            || echo "  (system: нет доступа, нужен root)"
        dmidecode -t bios 2>/dev/null | grep -E 'Vendor|Version|Release Date|Runtime Size' \
            || echo "  (bios: нет доступа, нужен root)"
    else
        echo "  (dmidecode нет)"
    fi
    echo

    echo "## Режим загрузки и Secure Boot"
    if [ "$HAVE_EFI" -eq 1 ]; then
        echo "UEFI: да"
        # efivars: 4 байта GUID-атрибутов, затем значение; последний байт — 1/0
        SB_FOUND=0
        for f in /sys/firmware/efi/efivars/SecureBoot-*; do
            [ -e "$f" ] || continue
            SB_FOUND=1
            v="$(od -An -tu1 -j4 -N1 "$f" 2>/dev/null | tr -d ' ')"
            echo "SecureBoot: ${v:-не прочитано}"
        done
        [ "$SB_FOUND" -eq 1 ] || echo "SecureBoot: переменная недоступна (нужен root или выключен)"
        command -v mokutil >/dev/null 2>&1 \
            && mokutil --sb-state 2>/dev/null \
            || echo "mokutil: нет"
        command -v efibootmgr >/dev/null 2>&1 \
            && efibootmgr -v 2>/dev/null | head -30 \
            || echo "efibootmgr: нет — загрузочные записи не сняты"
    else
        echo "UEFI: нет (Legacy/CSM или нет доступа)"
    fi
    echo

    echo "## TPM"
    if [ -r /sys/class/tpm/tpm0/tpm_version_major ]; then
        echo "TPM: версия $(cat /sys/class/tpm/tpm0/tpm_version_major)"
    else
        echo "TPM: не виден из этой среды"
    fi
    [ "$HAVE_TPM" -eq 1 ] && tpm2_pcrread sha256:0,1,2,4,7,11 2>/dev/null | head -40 \
        || echo "  (tpm2-tools нет — PCR не сняты)"
    echo

    echo "## Intel ME"
    echo "  Из Linux версия ME штатно не читается. Снимается в Windows:"
    echo "    Get-WmiObject -Namespace root\\WMI -Class MEVersion"
    echo "  либо утилитой MEInfoWin из Intel ME System Tools."
    echo

    echo "## Накопители"
    if command -v nvme >/dev/null 2>&1; then
        nvme list 2>/dev/null || echo "  (nvme list: нет доступа)"
    else
        echo "  nvme-cli нет — версии прошивок NVMe не сняты"
    fi
    if command -v smartctl >/dev/null 2>&1; then
        for d in /dev/sd? /dev/nvme?n1; do
            [ -e "$d" ] || continue
            echo "--- $d"
            smartctl -i "$d" 2>/dev/null | grep -Ei 'Model|Serial|Firmware' \
                || echo "  (нет доступа)"
        done
    else
        echo "  smartctl нет — версии прошивок SATA не сняты"
    fi
    echo

    echo "## Настройки UEFI, которые надо вернуть после прошивки"
    cat <<'SETTINGS'
Прошивка возвращает настройки UEFI к значениям по умолчанию. До прошивки
записать от руки, после — вернуть:

  [ ] Secure Boot: состояние и режим ключей (Standard / Custom)
  [ ] Порядок загрузки и загрузочная запись Windows
  [ ] CSM / Legacy: выключен или включён
  [ ] Intel VMD controller: Enabled / Disabled  <-- критично для установки
      Windows на MSI 11-го поколения и новее: при VMD=Enabled нужен драйвер
      IRST/VMD в образе, иначе установщик не видит накопитель
  [ ] SATA Mode: AHCI / RAID
  [ ] Fast Boot
  [ ] Пароль BIOS, если задан
  [ ] XMP/EXPO и прочие профили памяти
SETTINGS
} > "$REPORT.tmp" 2>&1

if [ "$DRYRUN" -eq 1 ]; then
    echo "--- [dry-run] содержимое отчёта ---"
    cat "$REPORT.tmp"
    rm -f "$REPORT.tmp"
    echo "--- [dry-run] файл не сохранён ---"
    exit 0
fi

mv "$REPORT.tmp" "$REPORT"
LINES=$(wc -l < "$REPORT" | tr -d ' ')
echo "Готово: $REPORT ($LINES строк)"
echo "Скопировать на Tools: и приложить к algorithm.md станции."
exit 0
