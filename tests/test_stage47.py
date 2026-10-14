# -*- coding: utf-8 -*-
"""Проверки группы tools/backup/ (Этап 4.7).

Строить на этапе оказалось нечего: группа наполнена на Этапе 3c, синхронизацию
заказчик снял. Тест фиксирует решения, чтобы вопросы не поднялись заново.
"""
import csv, io, os, re, sys

ROOT = '/home/user/immutable_workstation2'
os.chdir(ROOT)
checks = errors = 0


def ok(m):
    global checks
    checks += 1
    print('  OK   ' + m)


def bad(m):
    global checks, errors
    checks += 1
    errors += 1
    print('  FAIL ' + m)


def t(cond, m):
    ok(m) if cond else bad(m)


BK = 'tools/backup'
SUBS = ['disk_image', 'drivers', 'initial_backup', 'profiles']

print('[1] Структура группы')
t(os.path.isfile(f'{BK}/README.md'), 'есть индекс группы')
for s in SUBS:
    t(os.path.isdir(f'{BK}/{s}'), f'есть подкатегория {s}/')
    t(os.path.isfile(f'{BK}/{s}/README.md'), f'есть индекс {s}/README.md')

print('\n[2] Индекс группы перечисляет все четыре подкатегории в одной таблице')
idx = io.open(f'{BK}/README.md', encoding='utf-8').read()
t('## Состав' not in idx,
  'отдельной таблицы «Состав» больше нет — initial_backup в общей таблице')
for s in SUBS:
    t(f'| `{s}/`' in idx, f'в таблице подкатегорий есть {s}/')

print('\n[3] Решение по синхронизации записано')
t('Чего в группе нет намеренно' in idx, 'есть раздел про намеренное отсутствие')
t('Синхронизации нет' in idx, 'сказано прямо, что синхронизации нет')
t('Решение заказчика от 2026-10-11' in idx, 'названа дата решения')
t('FreeFileSync' in idx, 'назван FreeFileSync как единственный кандидат')
t('снимк' in idx.lower() and 'синхронизаци' in idx.lower(),
  'объяснено отличие снимка от синхронизации')
t('/MIR' in idx and '--yes' in idx,
  'записано, что зеркалирование допустимо только через --yes')
t('research/12-backup-imaging-sync.md' in idx, 'есть ссылка на исследование')
t(os.path.isfile('research/12-backup-imaging-sync.md'), 'исследование на месте')

print('\n[4] Модуля синхронизации действительно нет')
stray = []
for root, dirs, files in os.walk(BK):
    for f in files:
        low = f.lower()
        if any(k in low for k in ('sync', 'mirror', 'robocopy')):
            stray.append(os.path.join(root, f))
t(not stray, 'файлов с sync/mirror/robocopy в backup/ нет'
    + (f' -> {stray}' if stray else ''))
dirs = []
for root, dlist, _f in os.walk(BK):
    for d in dlist:
        if 'sync' in d.lower():
            dirs.append(os.path.join(root, d))
t(not dirs, 'каталога sync/ нет' + (f' -> {dirs}' if dirs else ''))
rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))[1:]
t(not [r for r in rows if r[1].startswith('backup/') and 'sync' in r[2].lower()],
  'в manifest нет сущности синхронизации')

print('\n[5] Модули Этапа 3c на месте и парные')
MODS = ['backup-chrome', 'backup-vscode', 'export-drivers', 'verify-backup']
SC = f'{BK}/initial_backup/scripts'
for m in MODS:
    t(os.path.isfile(f'{SC}/{m}.ps1'), f'{m}.ps1 на месте')
    t(os.path.isfile(f'{SC}/{m}.sh'), f'{m}.sh на месте')
t(os.path.isfile(f'{BK}/disk_image/scripts/disk-image.sh'),
  'disk-image.sh на месте')
t(not os.path.isfile(f'{BK}/disk_image/scripts/disk-image.ps1'),
  'disk-image.ps1 нет — исключение зафиксировано')

print('\n[6] Правило группы не ослаблено')
t('ничего не удаляет и не перезаписывает без явного' in idx,
  'правило «не удалять без явного флага» на месте')
t('SHA256' in idx, 'требование манифеста SHA256 на месте')

print('\n[7] manifest и tools/README.md согласованы')
tr = io.open('tools/README.md', encoding='utf-8').read()
line = [l for l in tr.splitlines() if l.startswith('| `backup/`')]
t(len(line) == 1, 'в tools/README.md одна строка для группы backup/')
if line:
    for s in SUBS:
        t(s in line[0], f'в строке backup/ названа подкатегория {s}')
on_disk = sorted(os.listdir(BK))
on_disk = [x for x in on_disk if os.path.isdir(os.path.join(BK, x))]
t(sorted(SUBS) == on_disk, f'подкатегорий на диске столько же: {on_disk}')

print('\n[8] Этап 4.7 закрыт в PLAN.md')
pl = io.open('PLAN.md', encoding='utf-8').read()
m47 = re.search(r'^## Этап 4\.7 — backup (.*)$', pl, re.M)
t(m47 is not None, 'в PLAN.md есть раздел Этапа 4.7')
if m47:
    t('✅' in m47.group(1), f'Этап 4.7 отмечен выполненным: «{m47.group(1)}»')
t('Синхронизация' in pl and 'Не делать' in pl,
  'решение по синхронизации записано в плане')
t('Не трогать' in pl, 'решение по лицензиям Strelec записано в плане')
t('остаются неразобранными' in pl,
  'в плане честно сказано, что лицензии средств клонирования не разобраны')

print('\n[9] Регрессия: предыдущие этапы целы')
for p in ['tools/drivers/packs/SDIO/README.md',
          'tools/security/scanner/README.md',
          'tests/test_rules.py',
          'research/12-backup-imaging-sync.md']:
    t(os.path.isfile(p), f'на месте {p}')
names = [r[2] for r in rows]
for n in ['SDIO', 'SDIO-drivers', 'VeraCrypt', 'initial_backup', 'disk_image']:
    t(n in names, f'в manifest осталась сущность {n}')
t(len(rows) == 40, f'строк данных по-прежнему 40 (факт {len(rows)})')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
