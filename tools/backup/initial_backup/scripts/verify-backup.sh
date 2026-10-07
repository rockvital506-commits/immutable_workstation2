#!/usr/bin/env bash
# ============================================================
# verify-backup.sh — проверка целостности бэкапа по манифесту SHA256
#
# Парная версия verify-backup.ps1.
#
# Запуск:
#   bash verify-backup.sh --path /mnt/tools/backup/profiles/chrome_2026-10-07_12-00-00
#
# Коды возврата: 0 — копия цела, 1 — есть расхождения, 3 — манифест не найден.
# ============================================================
set -uo pipefail

BACKUP='' MANIFEST_NAME='_manifest.sha256.csv'

usage() { sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -p|--path)     BACKUP="${2:?}"; shift 2 ;;
        -m|--manifest) MANIFEST_NAME="${2:?}"; shift 2 ;;
        -h|--help)     usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

[ -n "$BACKUP" ] || { echo 'Нужен --path' >&2; usage 1; }
[ -d "$BACKUP" ] || { echo "ОШИБКА: каталог не найден: $BACKUP" >&2; exit 3; }

MANIFEST="$BACKUP/$MANIFEST_NAME"
[ -f "$MANIFEST" ] || { echo "ОШИБКА: манифест не найден: $MANIFEST" >&2; exit 3; }

ERRORS=0 OKS=0

# Разбор CSV с учётом кавычек: path,sha256,size_bytes,captured_at
while IFS= read -r line; do
    rel="${line%%,*}"
    rest="${line#*,}"
    expected="${rest%%,*}"
    [ -z "$rel" ] && continue

    full="$BACKUP/$rel"
    if [ ! -f "$full" ]; then
        printf '  \033[31mFAIL\033[0m отсутствует: %s\n' "$rel"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    actual="$(sha256sum "$full" | awk '{print $1}' | tr 'A-F' 'a-f')"
    if [ "$actual" = "$(printf '%s' "$expected" | tr 'A-F' 'a-f')" ]; then
        OKS=$((OKS + 1))
    else
        printf '  \033[31mFAIL\033[0m хэш не совпадает: %s\n' "$rel"
        ERRORS=$((ERRORS + 1))
    fi
done < <(tail -n +2 "$MANIFEST")

EXTRA=0
while IFS= read -r f; do
    rel="${f#"$BACKUP"/}"
    case "$rel" in
        "$MANIFEST_NAME"|_RESTORE_NOTES.md) continue ;;
    esac
    if ! grep -q "^$rel," "$MANIFEST"; then
        printf '  \033[33mWARN\033[0m не в манифесте: %s\n' "$rel"
        EXTRA=$((EXTRA + 1))
    fi
done < <(find "$BACKUP" -type f)

echo
echo "Итог: совпало $OKS, расхождений $ERRORS, вне манифеста $EXTRA"
if [ "$ERRORS" -gt 0 ]; then
    printf '\033[31mКопия повреждена или неполна — использовать её нельзя.\033[0m\n'
    exit 1
fi
printf '\033[32mКопия цела.\033[0m\n'
exit 0
