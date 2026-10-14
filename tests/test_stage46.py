# -*- coding: utf-8 -*-
"""Проверки группы tools/drivers/ (Этап 4.6)."""
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


DRV = 'tools/drivers'
SUBS = ['packs', 'export']
UTIL = ('packs', 'SDIO')
PACK = ('packs', 'SDIO-drivers')
STUBS = ['SDIO_2.0.4.887.zip.md']
PACK_STUBS = ['Drivers.torrent.md']
REQ = ['## Назначение', '## Состав каталога', '## Версия и источник',
       '## Аналоги', '## История изменений']

print('[1] Структура группы')
t(os.path.isfile(f'{DRV}/README.md'), 'есть индекс группы')
for s in SUBS:
    t(os.path.isdir(f'{DRV}/{s}'), f'есть подкатегория {s}/')
    t(os.path.isfile(f'{DRV}/{s}/README.md'), f'есть индекс {s}/README.md')
d = f'{DRV}/{UTIL[0]}/{UTIL[1]}'
t(os.path.isdir(d), f'есть каталог утилиты {d}')
t(os.path.isfile(f'{d}/README.md'), f'есть {d}/README.md')
for stub in STUBS:
    t(os.path.isfile(f'{d}/{stub}'), f'есть заглушка {d}/{stub}')
t(not os.path.isfile(f'{DRV}/packs/SDIO_2.0.4.887.zip.md'),
  'заглушки не остались в корне packs/ — утилита оформлена папкой')
pd = f'{DRV}/{PACK[0]}/{PACK[1]}'
t(os.path.isdir(pd), f'есть каталог пака {pd}')
t(os.path.isfile(f'{pd}/README.md'), f'есть {pd}/README.md')
for stub in PACK_STUBS:
    t(os.path.isfile(f'{pd}/{stub}'), f'есть заглушка {pd}/{stub}')
t(not os.path.isfile(f'{d}/Drivers.torrent.md'),
  'пак не лежит в папке SDIO — он отдельная сущность')

print('\n[2] README утилиты заполнен по шаблону')
s = io.open(f'{d}/README.md', encoding='utf-8').read()
missing = [r for r in REQ if r not in s]
t(not missing, 'все обязательные разделы' + (f' (нет: {missing})' if missing else ''))
probe = re.sub(r'https?://\S+', '', s)
found = [m for m in re.findall(r'<([^<>\n]{1,40})>', probe) if m.strip() and ' ' not in m]
t(not found, 'нет незаполненных плейсхолдеров' + (f' -> {found}' if found else ''))

print('\n[3] Решения заказчика отражены')
grp = io.open(f'{DRV}/README.md', encoding='utf-8').read()
t('Онлайн-установщики вендоров' in grp, 'в индексе сказано, что онлайн-установщики не взяты')
t('Intel Driver & Support Assistant' in grp, 'назван Intel DSA')
t('MSI Center' in grp, 'назван MSI Center')
t('DriverPack Solution' in grp, 'в индексе назван исключённый DriverPack Solution')
t('builds/' in grp, 'драйверы станции отправлены в builds/')
t('pnputil' in grp, 'в индексе назван pnputil как основной слой')
packs = io.open(f'{DRV}/packs/README.md', encoding='utf-8').read()
t('GPL' in packs, 'в packs/ названа лицензия GPL')
t('Expert Mode' in packs or 'по умолчанию' in packs,
  'в packs/ объяснено, почему DriverPack исключён')
exp = io.open(f'{DRV}/export/README.md', encoding='utf-8').read()
t('Утилит здесь нет' in exp, 'в export/ объяснено отсутствие утилит')
t('pnputil /add-driver' in exp, 'в export/ есть установка из INF')
t('/enum-devices /problem' in exp, 'в export/ есть поиск проблемных устройств')
t('Export-Driver' in exp, 'в export/ есть выгрузка драйверов')
t('Add-Driver' in exp, 'в export/ есть интеграция в образ')
t('/Recurse' in exp, 'в export/ упомянут обязательный /Recurse')
t('export-drivers' in exp, 'в export/ есть ссылка на модуль бэкапа')

print('\n[4] Размер пака не занижен')
for p in [f'{pd}/README.md', f'{pd}/Drivers.torrent.md']:
    txt = io.open(p, encoding='utf-8').read()
    t('50' in txt, f'{os.path.basename(p)}: фигурируют 50 ГБ')
    t('расходятся' in txt, f'{os.path.basename(p)}: расхождение источников названо')
    t('25' in txt, f'{os.path.basename(p)}: прежнее значение 25 ГБ показано как одна из оценок')
u = io.open(f'{d}/README.md', encoding='utf-8').read()
t('50' in u, 'в README программы назван порядок размера пака')
pk = io.open(f'{pd}/README.md', encoding='utf-8').read()
t('50,0 ГБ' in pk and 'sdi-tool.org' in pk,
  'в README пака названы 50,0 ГБ и источник')
t('25' in pk, 'в README пака прежнее значение 25 ГБ показано как одна из оценок')

print('\n[5] Честность по версии и первоисточнику')
t('не сверена с первоисточником' in u, 'версия SDIO помечена несверенной')
t('SourceForge' in u, 'названа причина: SourceForge недоступен')
t('Origin' in u and 'samlab-ws' in u, 'развилка SDI/SDIO разобрана')
t('2.0.4.887' in u, 'версия 2.0.4.887 указана')
t('SDIO-drivers' in u, 'в README программы есть ссылка на пак')
t('sdi-tool.org' not in u,
  'таблица размеров пака не дублируется в README программы — она одна, в SDIO-drivers')

print('\n[6] Заглушки')
for stub, base in [(x, d) for x in STUBS] + [(x, pd) for x in PACK_STUBS]:
    txt = io.open(f'{base}/{stub}', encoding='utf-8').read()
    t('CONVENTIONS' in txt, f'{stub}: ссылка на CONVENTIONS.md')
    t('PENDING' in txt, f'{stub}: SHA256 помечен PENDING')
    t('SHA256' in txt and 'Источник' in txt, f'{stub}: обязательные поля на месте')
    t('Как получить' in txt, f'{stub}: есть раздел «Как получить»')
    t('Куда положить на флешке' in txt, f'{stub}: есть раздел про размещение')
    t('Tools:\\drivers\\packs\\' in txt, f'{stub}: путь на флешке указан')

print('\n[7] manifest.csv')
raw = open('manifest.csv', 'rb').read()
t(b'\r\n' not in raw, 'manifest.csv в LF, без CRLF')
rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
head, body = rows[0], rows[1:]
t(len(body) == 36, f'36 строк данных (факт {len(body)})')
t(all(len(r) == 10 for r in body), 'во всех строках 10 полей')
sдио = [r for r in body if r[1] == 'drivers/packs']
t(len(sдио) == 2, f'две строки drivers/packs (факт {len(sдио)})')
pairs = sorted((r[2], r[3]) for r in sдио)
t(pairs == [('SDIO', 'SDIO_2.0.4.887.zip'), ('SDIO-drivers', 'Drivers.torrent')],
  f'имена и файлы верны: {pairs}')
names = [r[2] for r in body]
t(len(set(names)) == len(names), 'имена в manifest уникальны — правило не сломано')
for r in sдио:
    t(r[0] == 'tool', f'{r[3]}: type=tool')
    t(os.path.isdir(f'tools/{r[1]}/{r[2]}'), f'{r[3]}: каталог сущности существует')
    t(r[4].startswith('https://'), f'{r[3]}: url заполнен')
    t(r[9] == 'planned', f'{r[3]}: status=planned')
t(not [r for r in body if r[1] == 'drivers/export'],
  'у export/ нет строк: утилит там нет')

print('\n[8] tools/README.md и PLAN.md согласованы')
tr = io.open('tools/README.md', encoding='utf-8').read()
line = [l for l in tr.splitlines() if l.startswith('| `drivers/`')]
t(len(line) == 1, 'в tools/README.md одна строка для группы drivers/')
if line:
    for sb in SUBS:
        t(sb in line[0], f'в строке drivers/ названа подкатегория {sb}')
    t('4.6' in line[0], 'строка drivers/ ссылается на Этап 4.6')
    for old in ['`windows/`', '`chipset/`', 'Этап 7']:
        t(old not in line[0], f'в строке нет прежнего {old}')
pl = io.open('PLAN.md', encoding='utf-8').read()
m7 = re.search(r'^## Этап 7 — (.+)$', pl, re.M)
t(m7 is not None, 'в PLAN.md есть Этап 7')
if m7:
    t('Драйверы' not in m7.group(1),
      f'Этап 7 переименован, драйверы из него убраны: «{m7.group(1)}»')
t('Частично поглощён Этапом 4.6' in pl, 'в Этапе 7 объяснено, что сделано на 4.6')
t('офлайн-обновлений Windows (LCU/SSU)' in pl, 'остаток Этапа 7 не потерян')

print('\n[9] Скрипты на этом этапе не пишутся')
stray = []
for root, dirs, files in os.walk(DRV):
    for f in files:
        if f.endswith(('.ps1', '.sh')):
            stray.append(os.path.join(root, f))
t(not stray, 'в drivers/ нет .ps1/.sh' + (f' -> {stray}' if stray else ''))

print('\n[10] Регрессия: предыдущие этапы целы')
for p in ['tools/security/scanner/README.md',
          'tools/security/encryption/VeraCrypt/README.md',
          'tools/network/README.md',
          'tests/test_rules.py',
          'research/11-driver-packs.md',
          'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md']:
    t(os.path.isfile(p), f'на месте {p}')
names = [r[2] for r in body]
for n in ['VeraCrypt', 'Autoruns', 'TCPView', 'WinUtil', 'RustDesk']:
    t(n in names, f'в manifest осталась сущность {n}')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
