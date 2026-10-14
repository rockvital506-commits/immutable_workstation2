# -*- coding: utf-8 -*-
"""Проверки группы tools/firmware/ (Этап 4.8).

Решения заказчика от 2026-10-14:
  1. Охват группы — ТОЛЬКО BIOS/UEFI материнской платы.
  2. Файл прошивки — на отдельной маленькой FAT32-флешке, наша не годится.
  3. Домашние роутеры из группы исключены.
  4. Категория ISO/firmware/ не создаётся.

Обоснование — research/14-firmware-update.md.
"""
import csv, io, os, subprocess, sys

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


FW = 'tools/firmware'
BIOS = 'tools/firmware/bios'
SH = f'{BIOS}/scripts/bios-inventory.sh'
PS = f'{BIOS}/scripts/bios-inventory.ps1'

rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
body = rows[1:]

print('[1] Структура группы: одна подкатегория')
t(os.path.isfile(f'{FW}/README.md'), 'есть индекс группы')
t(os.path.isdir(BIOS), 'есть подкатегория bios/')
t(os.path.isfile(f'{BIOS}/README.md'), 'есть индекс bios/README.md')
t(os.path.isfile(f'{BIOS}/fat32-stick.md'), 'есть fat32-stick.md')
subdirs = sorted(d for d in os.listdir(FW) if os.path.isdir(f'{FW}/{d}'))
t(subdirs == ['bios'], f'подкатегория ровно одна (факт {subdirs})')

print('\n[2] Решение «только BIOS/UEFI» зафиксировано и соблюдено')
fw = io.open(f'{FW}/README.md', encoding='utf-8').read()
for needle, what in [
    ('только BIOS/UEFI', 'охват сужен до BIOS/UEFI'),
    ('нет намеренно', 'есть раздел о том, чего нет'),
    ('NVMe', 'отказ от NVMe объяснён'),
    ('fwupd', 'отказ от fwupd объяснён'),
    ('роутер', 'отказ от роутеров объяснён'),
    ('14-firmware-update', 'ссылка на исследование'),
]:
    t(needle in fw, what)

print('\n[3] Роутеры исключены, а не просто не сделаны')
t('исключить' in fw.lower() or 'исключены' in fw.lower(),
  'в индексе группы сказано про исключение')
t('записать текущую версию прошивки роутера' in fw,
  'в алгоритме остаётся только запись версии')

print('\n[4] ISO/firmware/ не создаётся')
t(not os.path.isdir('ventoy-partition/ISO/firmware'),
  'каталога ISO/firmware/ нет')
iso = io.open('ventoy-partition/ISO/README.md', encoding='utf-8').read()
t('| `firmware/` |' not in iso,
  'строки firmware/ нет в таблице категорий ISO')
t('исключена' in iso, 'в ISO/README объяснено, что категория исключена')
t('fat32-stick' in iso, 'из ISO/README есть указание на отдельную флешку')

print('\n[5] Ограничение exFAT описано во всех трёх местах')
bios = io.open(f'{BIOS}/README.md', encoding='utf-8').read()
stick = io.open(f'{BIOS}/fat32-stick.md', encoding='utf-8').read()
for name, txt in [('индекс группы', fw), ('bios/README', bios),
                  ('fat32-stick', stick)]:
    t('FAT32' in txt, f'{name}: FAT32 назван требованием')
    t('exFAT' in txt, f'{name}: объяснено, что exFAT не читается')
t('VTOYEFI' in fw or 'FAT16' in fw, 'в индексе группы назван и FAT16-раздел')
t('Вторая флешка' in stick or 'вторая' in stick.lower(),
  'решение заказчика названо в fat32-stick.md')

print('\n[6] Процедура обновления соответствует официальному источнику MSI')
for needle, what in [
    ('Advanced', 'путь Advanced -> UEFI BIOS Update'),
    ('UEFI BIOS Update', 'название пункта меню'),
    ('Load Optimized Defaults', 'сброс настроек до прошивки'),
    ('Proceed with flash update', 'шаг после перезагрузки'),
    ('Не переименовывать', 'запрет переименования файла'),
    ('MSI.ROM', 'объяснено, когда MSI.ROM всё-таки нужен'),
    ('Delete', 'клавиша входа в BIOS'),
]:
    t(needle in bios, what)

print('\n[7] BitLocker и восстановление')
for needle, what in [
    ('Suspend-BitLocker', 'команда приостановки'),
    ('Resume-BitLocker', 'команда возобновления'),
    ('один раз на весь выезд', 'правило однократной приостановки'),
    ('PCR', 'объяснена связь с PCR'),
]:
    t(needle in bios, what)
for needle, what in [
    ('fptw64', 'бэкап SPI через Intel FPT'),
    ('Только восстановление', 'FPT — не штатный путь'),
    ('Error 25', 'предупреждение о блокировке записи'),
    ('drvload HECI.inf', 'загрузка драйвера в WinPE'),
    ('Лицензия не проверена', 'лицензия FPT помечена непроверенной'),
]:
    t(needle in bios, what)

print('\n[8] Скрипт инвентаризации: пара на месте')
t(os.path.isfile(SH), SH)
t(os.path.isfile(PS), PS)
for p in [SH, PS]:
    t(os.path.getsize(p) > 2000, f'{p}: не заглушка ({os.path.getsize(p)} байт)')
sh = io.open(SH, encoding='utf-8').read()
ps = io.open(PS, encoding='utf-8').read()
for name, txt, needles in [
    ('.sh', sh, ['#!/usr/bin/env bash', 'set -euo pipefail', 'LOG_FILE=',
                 'tee -a', 'exec bash "$0" "$@"', 'DRYRUN']),
    ('.ps1', ps, ['#Requires', 'CmdletBinding', '$ErrorActionPreference',
                  'Start-Transcript', '-Append', 'PowerShell.Exiting']),
]:
    for n in needles:
        t(n in txt, f'{name}: есть {n}')

print('\n[9] Скрипт ничего не прошивает')
for name, txt in [('.sh', sh), ('.ps1', ps)]:
    danger = [w for w in ('fptw64', 'afudos', 'fw-download', 'fw-commit',
                          'Add-WindowsPackage', '/Add-Package')
              if w in txt]
    t(not danger, f'{name}: средств прошивки нет' + (f' -> {danger}' if danger else ''))
t('VMD' in sh and 'VMD' in ps, 'в чек-листе есть Intel VMD controller')
t('MEVersion' in ps, '.ps1 снимает версию Intel ME')
t('Intel ME' in sh, '.sh объясняет, что ME из Linux не читается')

print('\n[10] .sh исполняется: коды возврата')
os.system('rm -rf /tmp/t48 && mkdir -p /tmp/t48/out /tmp/t48/bin')
io.open('/tmp/t48/bin/dmidecode', 'w').write(
    '#!/bin/sh\ncase "$2" in\n'
    '  system) printf "\\tManufacturer: MSI\\n\\tProduct Name: Test\\n" ;;\n'
    '  bios)   printf "\\tVersion: E0000IMS.100\\n" ;;\n'
    'esac\n')
os.chmod('/tmp/t48/bin/dmidecode', 0o755)
env = dict(os.environ, PATH='/tmp/t48/bin:' + os.environ['PATH'])


def run(args, use_env=True):
    p = subprocess.run(['bash', SH] + args, capture_output=True, text=True,
                       env=env if use_env else None)
    return p.returncode, p.stdout + p.stderr


code, out = run(['--help'])
t(code == 0, f'--help даёт 0 (факт {code})')
t('set -euo pipefail' not in out, '--help не выводит строки вне шапки')

code, out = run([], use_env=False)
t(code == 2, f'без средств инвентаризации — 2 (факт {code})')

code, out = run(['--out', '/tmp/t48/нет-такого'])
t(code == 3, f'недоступный каталог — 3 (факт {code})')

code, out = run(['--bogus'])
t(code == 1, f'неизвестный параметр — 1 (факт {code})')

code, out = run(['--out', '/tmp/t48/out'])
t(code == 0, f'реальный прогон — 0 (факт {code})')
made = [f for f in os.listdir('/tmp/t48/out') if f.startswith('bios-inventory-')]
t(len(made) == 1, f'отчёт создан ({made})')
if made:
    rep = io.open(f'/tmp/t48/out/{made[0]}', encoding='utf-8').read()
    for needle in ['E0000IMS.100', 'Intel VMD controller', 'Secure Boot',
                   '## Накопители']:
        t(needle in rep, f'в отчёте есть «{needle}»')

code, out = run(['--out', '/tmp/t48/out', '--dry-run'])
t(code == 0, f'--dry-run — 0 (факт {code})')
t('[dry-run]' in out, '--dry-run помечает вывод')
after = [f for f in os.listdir('/tmp/t48/out') if f.startswith('bios-inventory-')]
t(len(after) == 1, f'--dry-run не оставил файл (факт {len(after)})')
t(not os.path.isfile('/tmp/t48/out/bios-inventory.sh.log.tmp'),
  'временных файлов не осталось')

print('\n[11] Сущности в manifest.csv')
mine = [r for r in body if r[1] == 'firmware/bios']
t(len(mine) == 2, f'две строки firmware/bios (факт {len(mine)})')
types = sorted(r[0] for r in mine)
t(types == ['module', 'script'], f'module и script (факт {types})')
for r in mine:
    t(r[2] == 'bios_update' if r[0] == 'module' else r[2] == 'bios-inventory',
      f"{r[0]}: имя {r[2]}")
    t(r[3] == '' and r[4] == '', f'{r[2]}: file и url пусты — это своё')
    t(len(r[5]) == 64, f'{r[2]}: sha256 полной длины')
    t(int(r[6]) > 0, f'{r[2]}: size_bytes заполнен')
    t(r[9] == 'present', f'{r[2]}: status=present')
names = [r[2] for r in body]
t(len(set(names)) == len(names), 'имена в manifest уникальны')

print('\n[12] Регрессия: предыдущие этапы целы')
for p in ['tools/drivers/export/scripts/integrate-drivers.sh',
          'tools/os/windows/updates/offline-procedure.md',
          'tools/security/encryption/README.md',
          'research/14-firmware-update.md',
          'tests/test_stage7.py']:
    t(os.path.isfile(p), f'на месте {p}')
t(len(body) == 41, f'строк данных 39 (факт {len(body)})')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
