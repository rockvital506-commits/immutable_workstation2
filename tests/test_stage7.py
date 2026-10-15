# -*- coding: utf-8 -*-
"""Проверки остатка Этапа 7 — офлайн-обновления Windows и интеграция драйверов.

Этап закрыт двумя решениями заказчика от 2026-10-14:
  1. Каталог офлайн-обновлений на флешке НЕ заводится — вместо него процедура
     (где взять, как назвать, как проверить SHA256, как поставить через DISM).
  2. Скрипт интеграции — ТОЛЬКО драйверы, без /Add-Package.

Обоснование — research/13-offline-updates.md.
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


PROC = 'tools/os/windows/updates/offline-procedure.md'
SH = 'tools/drivers/export/scripts/integrate-drivers.sh'
PS = 'tools/drivers/export/scripts/integrate-drivers.ps1'

rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
body = rows[1:]

print('[1] Каталог офлайн-обновлений не заведён намеренно')
t(not os.path.isdir('tools/os/windows/updates/offline'),
  'каталога updates/offline/ в репозитории нет')
stray = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
    for f in files:
        if f.lower().endswith(('.msu', '.cab')):
            stray.append(os.path.join(root, f))
t(not stray, 'в репозитории нет .msu/.cab' + (f' -> {stray}' if stray else ''))
t(os.path.isfile(PROC), f'процедура на месте: {PROC}')

print('\n[2] Процедура отвечает на все четыре вопроса заказчика')
pr = io.open(PROC, encoding='utf-8').read()
for needle, what in [
    ('catalog.update.microsoft.com', 'где взять — Microsoft Update Catalog'),
    ('manifest.sha256.csv', 'как проверить SHA256 — манифест'),
    ('Get-FileHash', 'манифест считается штатным средством'),
    ('/Add-Package', 'как поставить — DISM /Add-Package'),
    ('Add-WindowsPackage', 'есть и PowerShell-вариант'),
    ('оставить как скачалось', 'как назвать файл'),
]:
    t(needle in pr, f'{what}')

print('\n[3] Процедура предупреждает о необратимом')
for needle, what in [
    ('SSU не удаляется', 'пакет с SSU не откатывается'),
    ('сначала SSU, потом LCU', 'порядок раздельной установки обязателен'),
    ('пакеты SSU не выпускаются', 'отдельного SSU для 2004+ нет'),
    ('не ставить обновления до пост-теста', 'пост-тест Центра обновления — раньше'),
    ('старое удалять', 'устаревшие пакеты удалять'),
]:
    t(needle.lower() in pr.lower(), what)

print('\n[4] Скрипт интеграции: пара на месте')
t(os.path.isfile(SH), f'{SH}')
t(os.path.isfile(PS), f'{PS}')
for p in [SH, PS]:
    t(os.path.getsize(p) > 1000, f'{p}: не заглушка ({os.path.getsize(p)} байт)')

print('\n[5] Скрипт в manifest.csv как script, а не как tool')
mine = [r for r in body if r[2] == 'integrate-drivers']
t(len(mine) == 1, f'ровно одна строка integrate-drivers (факт {len(mine)})')
for r in mine:
    t(r[0] == 'script', 'type=script')
    t(r[1] == 'drivers/export', 'category=drivers/export')
    t(r[3] == '' and r[4] == '', 'file и url пусты — это свой скрипт')
    t(len(r[5]) == 64, f'sha256 полной длины ({len(r[5])})')
    t(int(r[6]) > 0, f'size_bytes заполнен ({r[6]})')
    t(r[9] == 'present', 'status=present')

print('\n[6] Охват намеренно узкий: только драйверы')
for p in [SH, PS]:
    calls = []
    for line in io.open(p, encoding='utf-8').read().splitlines():
        st = line.strip()
        if st.startswith('#') or st.startswith('<#'):
            continue
        if '/Add-Package' in st or 'Add-WindowsPackage -' in st:
            calls.append(st)
    t(not calls, f'{p}: обновлений не ставит' + (f' -> {calls}' if calls else ''))
    txt = io.open(p, encoding='utf-8').read()
    t('/Add-Driver' in txt or 'Add-WindowsDriver' in txt,
      f'{p}: драйверы добавляет рекурсивно')
    t('/Recurse' in txt or '-Recurse' in txt, f'{p}: /Recurse присутствует')
    t('13-offline-updates' in txt, f'{p}: объяснено, почему обновлений нет')

print('\n[7] .sh исполняется: коды возврата')
FIX = '/tmp/test_stage7_fix'
os.system(f'rm -rf {FIX} && mkdir -p {FIX}/src/net {FIX}/win {FIX}/empty')
io.open(f'{FIX}/src/net/netwtw08.inf', 'w').write('[Version]\n')
io.open(f'{FIX}/fake.wim', 'w').write('')


def run(args):
    p = subprocess.run(['bash', SH] + args, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


code, out = run(['--help'])
t(code == 0, f'--help даёт 0 (факт {code})')
t('Коды возврата' in out, '--help печатает таблицу кодов возврата')

code, out = run([])
t(code == 1, f'без аргументов — 1 (факт {code})')

code, out = run(['--source', f'{FIX}/nope', '--offline', f'{FIX}/win'])
t(code == 3, f'несуществующий источник — 3 (факт {code})')

code, out = run(['--source', f'{FIX}/empty', '--offline', f'{FIX}/win'])
t(code == 3, f'источник без INF — 3 (факт {code})')
t('ни одного .inf' in out, 'сообщение объясняет причину')

code, out = run(['--source', f'{FIX}/src', '--image', f'{FIX}/fake.wim',
                 '--offline', f'{FIX}/win'])
t(code == 1, f'обе цели сразу — 1 (факт {code})')

code, out = run(['--source', f'{FIX}/src', '--image', f'{FIX}/fake.wim'])
t(code == 2, f'--image без DISM — 2 (факт {code})')

code, out = run(['--source', f'{FIX}/src', '--offline', f'{FIX}/win'])
t(code == 2, f'--offline без DISM — 2 (факт {code})')
t('Найдено INF: 1' in out, 'INF в источнике посчитан до проверки DISM')

print('\n[8] Скрипт не оставляет мусора и пишет лог')
t(not os.path.isdir('/tmp/integrate-drivers-mount'),
  'точка монтирования не создана при провале')
t(os.path.isfile('/tmp/integrate-drivers.sh.log'),
  'лог в /tmp/integrate-drivers.sh.log создан')

print('\n[9] Этап 7 закрыт в PLAN.md, исследование на месте')
pl = io.open('PLAN.md', encoding='utf-8').read()
t('Этап 7' in pl, 'Этап 7 упомянут в PLAN.md')
t('research/13-offline-updates.md' in pl or '13-offline-updates' in pl,
  'PLAN.md ссылается на исследование офлайн-обновлений')
t(os.path.isfile('research/13-offline-updates.md'),
  'research/13-offline-updates.md на месте')

print('\n[10] Регрессия: предыдущие этапы целы')
for p in ['tools/drivers/export/README.md', 'tools/drivers/packs/SDIO/README.md',
          'tools/drivers/packs/SDIO-drivers/README.md',
          'tools/os/windows/updates/README.md',
          'tools/backup/initial_backup/scripts/export-drivers.sh']:
    t(os.path.isfile(p), f'на месте {p}')
t(len(body) == 44, f'строк данных 37 (факт {len(body)})')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
