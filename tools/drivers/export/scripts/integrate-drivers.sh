#!/usr/bin/env bash
# ============================================================
# integrate-drivers.sh — добавление драйверов в образ Windows или в систему
#
# Парная версия integrate-drivers.ps1. Охват намеренно узкий: ТОЛЬКО драйверы.
# Обновления Windows (/Add-Package) этим скриптом не ставятся — у них другие
# последствия ошибки: драйвер снимается через `pnputil /delete-driver`,
# обновление с SSU не удаляется вовсе. См. research/13-offline-updates.md.
#
# В Linux DISM недоступен, поэтому режим --offline требует смонтированного
# каталога Windows-образа, а --online в Linux не поддерживается.
#
# Запуск:
#   sudo bash integrate-drivers.sh --source /mnt/tools/drivers --image /mnt/iso/sources/install.wim
#   sudo bash integrate-drivers.sh --source /mnt/tools/drivers --offline /mnt/win
#   sudo bash integrate-drivers.sh --source /mnt/tools/drivers --image ... --dry-run
#
# Коды возврата: 0 — успех, 1 — ошибка, 2 — нет прав или DISM, 3 — источник/образ недоступны.
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

SOURCE='' IMAGE='' MOUNT='' INDEX=1 DRYRUN=0 KEEP=0
DISM='dism'

usage() { sed -n '2,19p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -s|--source)      SOURCE="${2:?}"; shift 2 ;;
        -i|--image)       IMAGE="${2:?}";  shift 2 ;;
        -o|--offline)     MOUNT="${2:?}";  shift 2 ;;
        -x|--index)       INDEX="${2:?}";  shift 2 ;;
        --dry-run)        DRYRUN=1; shift ;;
        --keep-mount)     KEEP=1; shift ;;
        -h|--help)        usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

die() { echo "ОШИБКА: $*" >&2; exit "${2:-1}"; }
log() { echo "$*"; }
run() { if [ "$DRYRUN" -eq 1 ]; then echo "  [dry-run] $*"; else eval "$@"; fi; }

# --- Проверка аргументов ---------------------------------------------------
[ -n "$SOURCE" ] || { echo 'Нужен --source' >&2; usage 1; }
[ -d "$SOURCE" ] || die "каталог с драйверами не найден: $SOURCE" 3

if [ -n "$IMAGE" ] && [ -n "$MOUNT" ]; then
    die "--image и --offline одновременно не задаются: это разные цели" 1
fi
[ -n "$IMAGE" ] || [ -n "$MOUNT" ] || { echo 'Нужен --image или --offline' >&2; usage 1; }

# --- Считаем, что собираемся добавить -------------------------------------
INF_TOTAL=0
while IFS= read -r _inf; do
    INF_TOTAL=$((INF_TOTAL + 1))
done < <(find "$SOURCE" -type f -iname '*.inf')

log "Источник драйверов: $SOURCE"
log "Найдено INF: $INF_TOTAL"
if [ "$INF_TOTAL" -eq 0 ]; then
    die "в каталоге нет ни одного .inf — добавлять нечего" 3
fi

# --- Режим образа: нужен DISM ---------------------------------------------
if [ -n "$IMAGE" ]; then
    [ -f "$IMAGE" ] || die "образ не найден: $IMAGE" 3
    command -v "$DISM" >/dev/null 2>&1 || die "нет dism — режим --image доступен в Windows и WinPE" 2
    [ "$(id -u)" -eq 0 ] || die "требуются права root" 2

    MOUNTDIR="${TMPDIR:-/tmp}/integrate-drivers-mount"
    log "Образ: $IMAGE (индекс $INDEX)"
    log "Точка монтирования: $MOUNTDIR"

    run "mkdir -p '$MOUNTDIR'"
    run "$DISM /Mount-Image /ImageFile:'$IMAGE' /Index:$INDEX /MountDir:'$MOUNTDIR'"
    run "$DISM /Image:'$MOUNTDIR' /Add-Driver /Driver:'$SOURCE' /Recurse"

    if [ "$KEEP" -eq 1 ]; then
        log "--keep-mount: образ оставлен смонтированным в $MOUNTDIR"
        log "Завершить вручную: $DISM /Unmount-Image /MountDir:'$MOUNTDIR' /Commit"
    else
        run "$DISM /Unmount-Image /MountDir:'$MOUNTDIR' /Commit"
        run "rmdir '$MOUNTDIR'"
    fi

    log "Готово. Драйверов добавлено из каталога: $INF_TOTAL (INF)"
    log "Проверить в образе: $DISM /Image:<каталог> /Get-Drivers"
    exit 0
fi

# --- Режим установленной системы: только Windows --------------------------
if [ -n "$MOUNT" ]; then
    [ -d "$MOUNT" ] || die "каталог смонтированной системы не найден: $MOUNT" 3
    if ! command -v "$DISM" >/dev/null 2>&1; then
        die "нет dism. Из Linux драйверы в установленную Windows не добавляются; \
монтируйте Windows-раздел и запустите этот скрипт из WinPE, \
либо используйте pnputil из самой Windows" 2
    fi
    [ "$(id -u)" -eq 0 ] || die "требуются права root" 2

    log "Цель: смонтированная система $MOUNT"
    run "$DISM /Image:'$MOUNT' /Add-Driver /Driver:'$SOURCE' /Recurse"
    log "Готово. Драйверов добавлено из каталога: $INF_TOTAL (INF)"
    exit 0
fi
