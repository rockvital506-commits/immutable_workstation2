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
import re
import sys

VALID_TYPES = {"iso", "tool", "script", "module"}
VALID_STATUS = {"planned", "present", "verified", "deprecated"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EXPECTED_FIELDS = 10


def check(path: str) -> list[str]:
    problems: list[str] = []
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
