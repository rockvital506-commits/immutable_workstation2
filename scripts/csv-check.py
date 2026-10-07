#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv-check.py — проверка структуры manifest.csv (CONVENTIONS.md, раздел 4).

Использование:  python3 scripts/csv-check.py manifest.csv
Вывод: по одной строке на каждую найденную проблему; пустой вывод — ошибок нет.
Код возврата всегда 0: решение о падении принимает вызывающий скрипт.

Значения с запятыми внутри кавычек разбираются корректно (модуль csv),
поэтому проверка не даёт ложных срабатываний на URL и описаниях.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import sys

VALID_TYPES = {"iso", "tool", "script", "module"}
VALID_STATUS = {"planned", "present", "verified", "deprecated"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EXPECTED_FIELDS = 10

# Состав файлов наших сущностей (type=module|script).
# Хэш считается по конкатенации файлов в порядке сортировки путей,
# поэтому он воспроизводим и сверяем с manifest.csv.
SELF_ENTITIES = {
    "disk_image":     ["tools/backup/disk_image/scripts/disk-image.sh"],
    "initial_backup": ["tools/backup/initial_backup/scripts/export-drivers.sh"],
    "backup-chrome":  [
        "tools/backup/initial_backup/scripts/backup-chrome.ps1",
        "tools/backup/initial_backup/scripts/backup-chrome.sh",
    ],
    "backup-vscode":  ["tools/backup/initial_backup/scripts/backup-vscode.ps1"],
    "export-drivers": [
        "tools/backup/initial_backup/scripts/export-drivers.ps1",
        "tools/backup/initial_backup/scripts/export-drivers.sh",
    ],
    "verify-backup":  [
        "tools/backup/initial_backup/scripts/verify-backup.ps1",
        "tools/backup/initial_backup/scripts/verify-backup.sh",
    ],
    "disk-image":     ["tools/backup/disk_image/scripts/disk-image.sh"],
}


def self_hash(name: str, root: str) -> tuple[str, int] | None:
    """SHA256 и суммарный размер файлов сущности; None, если файла нет."""
    files = SELF_ENTITIES.get(name)
    if not files:
        return None
    digest = hashlib.sha256()
    total = 0
    for rel in sorted(files):
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            return None
        data = open(full, "rb").read()
        digest.update(data)
        total += len(data)
    return digest.hexdigest(), total


def check(path: str, root: str | None = None) -> list[str]:
    problems: list[str] = []
    if root is None:
        root = os.getcwd()
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    for lineno, row in enumerate(rows[1:], start=2):
        if not any(field.strip() for field in row):
            continue  # пустая строка в конце файла

        if len(row) != EXPECTED_FIELDS:
            problems.append(
                "строка %d: полей %d вместо %d — нарушен порядок колонок"
                % (lineno, len(row), EXPECTED_FIELDS)
            )
            continue

        rtype, _cat, name, file_, _url, sha256, size, _ver, added, status = row

        if rtype not in VALID_TYPES:
            problems.append("строка %d: type=%s недопустим" % (lineno, rtype))
        if status not in VALID_STATUS:
            problems.append("строка %d: status=%s недопустим" % (lineno, status))
        if not size.isdigit():
            problems.append("строка %d: size_bytes=%s не число" % (lineno, size))
        if not DATE_RE.match(added):
            problems.append("строка %d: added=%s не ГГГГ-ММ-ДД" % (lineno, added))
        if status != "planned" and sha256 == "PENDING":
            problems.append("строка %d: status=%s требует реальный SHA256" % (lineno, status))
        if status != "planned" and size == "0":
            problems.append("строка %d: status=%s требует реальный размер" % (lineno, status))
        if not name.strip():
            problems.append("строка %d: пустое name" % lineno)
        if rtype == "iso" and not file_.strip():
            problems.append("строка %d: для type=iso обязательно поле file" % lineno)

        # SELF-HASH: хэш наших скриптов и модулей обязан совпадать с файлами
        if rtype in ("module", "script") and name in SELF_ENTITIES and status == "present":
            got = self_hash(name, root)
            if got is None:
                problems.append("строка %d: файлы сущности %s не найдены" % (lineno, name))
            else:
                actual_sha, actual_size = got
                if sha256.lower() != actual_sha:
                    problems.append(
                        "строка %d: sha256 сущности %s расходится с файлами "
                        "(в манифесте %s, факт %s)" % (lineno, name, sha256[:12], actual_sha[:12])
                    )
                if size != str(actual_size):
                    problems.append(
                        "строка %d: size_bytes сущности %s расходится с файлами "
                        "(в манифесте %s, факт %d)" % (lineno, name, size, actual_size)
                    )

    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Использование: csv-check.py <manifest.csv>", file=sys.stderr)
        return 2
    for line in check(argv[1]):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
