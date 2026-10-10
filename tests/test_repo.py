#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Каркасные инварианты репозитория.

Проверяет то, что должно выполняться всегда, независимо от текущего этапа:
состав обязательных файлов, правило заглушек, целостность manifest.csv,
структуру ventoy.json, наличие algorithm.md у каждой станции, отсутствие
CJK-вкраплений и битых относительных ссылок.

Код возврата: 0 — всё в порядке, 1 — есть ошибки.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

checks = 0
errors = 0


def ok(msg: str) -> None:
    global checks
    checks += 1
    print('  OK   ' + msg)


def bad(msg: str) -> None:
    global checks, errors
    checks += 1
    errors += 1
    print('  FAIL ' + msg)


def t(cond: bool, msg: str) -> None:
    ok(msg) if cond else bad(msg)


# ---------------------------------------------------------------- 1. каркас
print('[1] Обязательные файлы и шаблоны')
for f in ['README.md', 'PLAN.md', 'CONVENTIONS.md', '.gitignore', 'manifest.csv',
          'ventoy-partition/ventoy/ventoy.json', 'ventoy-partition/ISO/README.md',
          'tools/README.md', 'research/README.md',
          'ventoy-partition/builds/README.md']:
    t(os.path.isfile(f), f'есть {f}')
for tpl in ['UTILITY_README.md', 'SCRIPT_README.md', 'MODULE_README.md']:
    t(os.path.isfile(f'tools/_templates/{tpl}'), f'есть шаблон tools/_templates/{tpl}')
t(os.path.isfile('ventoy-partition/builds/_templates/algorithm.md'),
  'есть шаблон builds/_templates/algorithm.md')

# ------------------------------------------------------- 2. правило заглушек
print('\n[2] Правило заглушек: <имя>.<расширение>.md + README рядом')
STUB = re.compile(r'^.+\.[A-Za-z0-9]+\.md$')
stubs = 0
for root, dirs, files in os.walk('.'):
    if root.startswith('./.git'):
        continue
    for f in files:
        if f == 'README.md' or not f.endswith('.md'):
            continue
        if not STUB.match(f):
            continue
        p = os.path.join(root, f)
        # служебные документы не являются заглушками бинарников
        if os.path.basename(root) in ('_templates', 'tests', 'scripts', 'research'):
            continue
        stubs += 1
        t(os.path.isfile(os.path.join(root, 'README.md')),
          f'рядом с {p} есть README.md')
t(stubs >= 7, f'заглушек бинарников найдено не меньше семи (факт {stubs})')

# ------------------------------------------------------------- 3. manifest
print('\n[3] manifest.csv')
raw = open('manifest.csv', 'rb').read()
t(b'\r\n' not in raw, 'manifest.csv в LF, без CRLF')
t(raw.endswith(b'\n'), 'manifest.csv заканчивается переводом строки')

rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
head, body = rows[0], rows[1:]
t(head == ['type', 'category', 'name', 'file', 'url', 'sha256',
           'size_bytes', 'version', 'added', 'status'],
  'заголовок manifest.csv соответствует CONVENTIONS.md')
t(all(len(r) == 10 for r in body),
  f'во всех {len(body)} строках по 10 полей')
names = [r[2] for r in body]
t(len(names) == len(set(names)), 'в manifest.csv нет дублей имён')

SHA = re.compile(r'^[0-9a-f]{64}$')
for r in body:
    typ, cat, name, _file, url, sha, size, ver, _added, status = r
    t(typ in ('tool', 'iso', 'module', 'script'), f'{name}: допустимый type={typ}')
    t(status in ('planned', 'present', 'verified'), f'{name}: допустимый status={status}')
    if status == 'planned':
        t(sha == 'PENDING' or SHA.match(sha), f'{name}: sha256 валиден')
    else:
        t(bool(SHA.match(sha)), f'{name}: status={status} требует реальный sha256')
        t(size.isdigit() and int(size) > 0, f'{name}: status={status} требует реальный размер')
    if typ == 'iso':
        t(bool(_file), f'{name}: для type=iso обязательно поле file')
    if typ == 'tool':
        t(os.path.isdir('tools/' + cat + '/' + name),
          f'{name}: каталог tools/{cat}/{name} существует')

# SELF-HASH: переиспользуем реализацию валидатора, а не копируем её
spec = importlib.util.spec_from_file_location('csvcheck', 'scripts/csv-check.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
problems = mod.check('manifest.csv', ROOT)
t(not problems, 'csv-check.py не нашёл расхождений' + (' -> ' + '; '.join(problems) if problems else ''))

# ----------------------------------------------------------- 4. ventoy.json
print('\n[4] ventoy/ventoy.json')
cfg = json.load(io.open('ventoy-partition/ventoy/ventoy.json', encoding='utf-8'))
t('control' in cfg, 'есть блок control')
ctl = cfg.get('control', [])
t(isinstance(ctl, list), 'control — список одноключевых объектов, как требует Ventoy')
t(len(ctl) >= 10, f'control содержит не меньше 10 опций (факт {len(ctl)})')
t(all(len(item) == 1 for item in ctl), 'в каждом элементе control ровно один ключ')
t(all(isinstance(v, str) for item in ctl for v in item.values()),
  'все значения control — строки, как требует Ventoy')
t('menu_alias' in cfg and len(cfg['menu_alias']) >= 5,
  f'есть menu_alias, не меньше пяти пунктов (факт {len(cfg.get("menu_alias", []))})')
t('persistence' in cfg, 'есть блок persistence')
if 'persistence' in cfg:
    for item in cfg['persistence']:
        t('image' in item and 'backend' in item, 'persistence: есть image и backend')
        t('autosel' in item and 'timeout' in item, 'persistence: есть autosel и timeout')
t('auto_install' in cfg, 'есть блок auto_install')
if 'auto_install' in cfg:
    for item in cfg['auto_install']:
        t('parent' in item, 'auto_install: правило задано через parent (image не работает)')
        t('timeout' not in item, 'auto_install: нет timeout (Ventoy его не отрабатывает)')
        t('template' in item, 'auto_install: указан template')

# ------------------------------------------------------------- 5. algorithm
print('\n[5] algorithm.md для каждой станционной сборки')
BUILDS = 'ventoy-partition/builds'
stations = [d for d in sorted(os.listdir(BUILDS))
            if os.path.isdir(os.path.join(BUILDS, d)) and d != '_templates']
t(len(stations) >= 1, f'найдена хотя бы одна станция (факт {len(stations)})')
SECTIONS = ['Порядок шагов', 'Валидация развёрнутой системы',
            'Рекомендации по дальнейшей эксплуатации', 'Не проверено на месте']
for st in stations:
    algo = os.path.join(BUILDS, st, 'algorithm.md')
    if not os.path.isfile(algo):
        bad(f'builds/{st}: нет algorithm.md (обязателен)')
        continue
    txt = io.open(algo, encoding='utf-8').read()
    for sec in SECTIONS:
        t(re.search(r'^## .*' + re.escape(sec), txt, re.M) is not None,
          f'builds/{st}: есть раздел «{sec}»')
    in_steps, tbl = False, ''
    for line in txt.splitlines():
        if re.match(r'^## .*Порядок шагов', line):
            in_steps = True
            continue
        if in_steps and line.startswith('## '):
            break
        if in_steps and line.startswith('|'):
            tbl += line + '\n'
    t('| Сеть |' in tbl.replace('  ', ' ') or re.search(r'\|\s*Сеть\s*\|', tbl),
      f'builds/{st}: в таблице шагов есть колонка «Сеть»')
    t(re.search(r'online|offline', tbl) is not None,
      f'builds/{st}: в таблице шагов есть статусы online/offline')

# --------------------------------------------------- 6. текст и ссылки
print('\n[6] Текст и относительные ссылки')
CJK = re.compile('[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')
bad_cjk, broken = [], []
for root, dirs, files in os.walk('.'):
    if root.startswith('./.git'):
        continue
    for f in files:
        p = os.path.join(root, f)
        if f.endswith(('.md', '.sh', '.ps1', '.py', '.json', '.csv')):
            try:
                txt = io.open(p, encoding='utf-8').read()
            except Exception:
                continue
            if CJK.search(txt):
                bad_cjk.append(p)
        if f.endswith('.md'):
            txt = io.open(p, encoding='utf-8').read()
            for m in re.finditer(r'\]\(([^)]+)\)', txt):
                link = m.group(1).split('#')[0]
                if not link or link.startswith(('http://', 'https://', 'mailto:')):
                    continue
                if not os.path.exists(os.path.normpath(os.path.join(root, link))):
                    broken.append(f'{p} -> {link}')
t(not bad_cjk, 'нет CJK-вкраплений' + (f': {bad_cjk}' if bad_cjk else ''))
t(not broken, 'нет битых относительных ссылок'
  + ('\n       ' + '\n       '.join(broken) if broken else ''))

# ------------------------------------------------------- 7. индексы tools
print('\n[7] Индексы в tools/')
for d in sorted(os.listdir('tools')):
    full = os.path.join('tools', d)
    if not os.path.isdir(full) or d == '_templates':
        continue
    t(os.path.isfile(os.path.join(full, 'README.md')), f'есть tools/{d}/README.md')
    for sub in sorted(os.listdir(full)):
        subfull = os.path.join(full, sub)
        if not os.path.isdir(subfull) or sub in ('_templates', 'scripts'):
            continue
        t(os.path.isfile(os.path.join(subfull, 'README.md')),
          f'есть tools/{d}/{sub}/README.md')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
