# -*- coding: utf-8 -*-
"""Проверки группы tools/os/windows/ (Этап 4.3)."""
import csv, io, os, re, sys

ROOT = '/home/user/immutable_workstation2'
os.chdir(ROOT)
checks = errors = 0
def ok(m):
    global checks; checks += 1; print('  OK   ' + m)
def bad(m):
    global checks, errors; checks += 1; errors += 1; print('  FAIL ' + m)
def t(cond, m):
    ok(m) if cond else bad(m)

OS = 'tools/os/windows'
SUBS = ['installation', 'activation', 'updates', 'tweaks', 'debloat', 'gpo_lock']
UTILS = {
    'WinUtil':       ('tweaks',    'winutil.ps1.md'),
    'Win11Debloat':  ('debloat',   'Win11Debloat.ps1.md'),
    'Sophia_Script': ('gpo_lock',  'Sophia.ps1.md'),
}

print('[1] Структура группы')
t(os.path.isfile(f'{OS}/README.md'), 'есть индекс группы')
for s in SUBS:
    t(os.path.isdir(f'{OS}/{s}'), f'есть подкатегория {s}/')
    t(os.path.isfile(f'{OS}/{s}/README.md'), f'есть индекс {s}/README.md')
for name, (sub, stub) in UTILS.items():
    d = f'{OS}/{sub}/{name}'
    t(os.path.isdir(d), f'есть каталог утилиты {d}')
    t(os.path.isfile(f'{d}/README.md'), f'есть {d}/README.md')
    t(os.path.isfile(f'{d}/{stub}'), f'есть заглушка {d}/{stub}')

print('\n[2] README утилит заполнены по шаблону')
REQ = ['## Назначение', '## Когда применять', '## Состав каталога', '## Запуск',
       '## Ключи и типовые сценарии', '## Результаты и как их читать',
       '## Риски и предупреждения', '## Версия и источник', '## Аналоги',
       '## История изменений']
for name, (sub, stub) in UTILS.items():
    s = io.open(f'{OS}/{sub}/{name}/README.md', encoding='utf-8').read()
    missing = [r for r in REQ if r not in s]
    t(not missing, f'{name}: все обязательные разделы' + (f' (нет: {missing})' if missing else ''))
    probe = re.sub(r'https?://\S+', '', s)
    found = [m for m in re.findall(r'<([^<>\n]{1,40})>', probe) if ' ' not in m.strip() and m.strip()]
    t(not found, f'{name}: нет незаполненных плейсхолдеров' + (f' -> {found}' if found else ''))
    t('SHA256' in s, f'{name}: есть строка SHA256')
    t('сверена с первоисточником' in s,
      f'{name}: помечено, что версия сверена с первоисточником')

print('\n[3] Заглушки')
for name, (sub, stub) in UTILS.items():
    s = io.open(f'{OS}/{sub}/{name}/{stub}', encoding='utf-8').read()
    t('CONVENTIONS' in s, f'{name}: ссылка на CONVENTIONS.md')
    t('PENDING' in s, f'{name}: SHA256 помечен PENDING')
    t('Как получить' in s, f'{name}: есть раздел «Как получить»')
    t('Куда положить на флешке' in s, f'{name}: есть раздел про размещение')

print('\n[4] manifest.csv')
raw = open('manifest.csv', 'rb').read()
t(b'\r\n' not in raw, 'manifest.csv в LF, без CRLF')
rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
head, body = rows[0], rows[1:]
# Этап 4.4 добавил 6 утилит группы network/: было 24, стало 30
t(len(body) == 30, f'30 строк данных (факт {len(body)})')
names = [r[2] for r in body]
t(len(set(names)) == len(names), 'нет дублей имён')
t(all(len(r) == 10 for r in body), 'во всех строках 10 полей')
EXPECT = {
    'WinUtil':       ('os/windows/tweaks',   'winutil.ps1',   '26.10.07'),
    'Win11Debloat':  ('os/windows/debloat',  'Win11Debloat.ps1', '2026.08.24'),
    'Sophia_Script': ('os/windows/gpo_lock', 'Sophia.ps1',    '7.3.0'),
}
by = {r[2]: r for r in body}
for name, (cat, f, ver) in EXPECT.items():
    t(name in by, f'{name}: есть строка в manifest.csv')
    r = by.get(name)
    if not r:
        continue
    t(r[0] == 'tool', f'{name}: type=tool')
    t(r[1] == cat, f'{name}: category={cat}')
    t(r[3] == f, f'{name}: file={f}')
    t(r[4].startswith('https://'), f'{name}: url заполнен')
    t(r[7] == ver, f'{name}: version={ver} (факт {r[7]})')
    t(r[9] == 'planned', f'{name}: status=planned')
    t(os.path.isdir(f'tools/{cat}/{name}'), f'{name}: каталог по category есть')

print('\n[5] Решения заказчика R1/R3/R4 зафиксированы в индексе группы')
g = io.open(f'{OS}/README.md', encoding='utf-8').read()
t('audit mode' in g.lower() or 'audit' in g, 'в индексе упомянут audit mode')
t('GTweak' in g, 'в индексе явно назван GTweak как невходящий в состав')
t('не входит' in g, 'в индексе зафиксирован отказ от GTweak')
t('Win11Debloat' in g and 'WinUtil' in g and 'Sophia' in g,
  'в индексе названы все три инструмента связки')
t('последовательно' in g, 'зафиксировано правило последовательного применения')
for s in ['installation', 'activation', 'updates', 'tweaks', 'debloat', 'gpo_lock']:
    t(f'({s}/)' in g, f'в индексе есть ссылка на {s}/')

print('\n[6] Содержание: конфликт инструментов и ключи реестра')
u = io.open(f'{OS}/updates/README.md', encoding='utf-8').read()
t('ExcludeWUDriversInQualityUpdate' in u, 'в updates/ есть ExcludeWUDriversInQualityUpdate')
t('IoT Enterprise LTSC' in u, 'в updates/ зафиксирована поддержка IoT Enterprise LTSC')
t('NoAutoRebootWithLoggedOnUsers' in u, 'в updates/ назван конфликтный ключ')
t('Конфликт с Win11Debloat' in u, 'в updates/ есть раздел о конфликте')
t('Не является документированной политикой' in u,
  'в updates/ ключи сообщества отделены от документированных')
t('Пост-тест Центра обновления' in u, 'в updates/ есть пост-тест WU')
t('AllowTelemetry' in u, 'в updates/ упомянут AllowTelemetry')
tw = io.open(f'{OS}/tweaks/README.md', encoding='utf-8').read()
t('Get-WinUtilTweaksStateReport' in tw, 'в tweaks/ названа функция отчёта WinUtil')
t('67' in tw, 'в tweaks/ указано число записей tweaks.json')
t('NOT FOR LAPTOPS' in tw, 'в tweaks/ есть предупреждение про ноутбуки')
db = io.open(f'{OS}/debloat/README.md', encoding='utf-8').read()
t('Apps.json' in db, 'в debloat/ упомянут Apps.json')
t('Undo' in db, 'в debloat/ упомянут каталог отката')
t('0x80073cf2' in db, 'в debloat/ упомянута ошибка sysprep')
gl = io.open(f'{OS}/gpo_lock/README.md', encoding='utf-8').read()
t('GroupPolicy' in gl, 'в gpo_lock/ назван каталог политик')
t('ACL' in gl, 'в gpo_lock/ описано закрепление через ACL')
t('способ снятия' in gl.lower() or 'снятия прав' in gl,
  'в gpo_lock/ требуется документировать способ снятия прав')
t('gpresult' in gl, 'в gpo_lock/ есть проверка через gpresult')
ins = io.open(f'{OS}/installation/README.md', encoding='utf-8').read()
t('260' in ins, 'в installation/ указан размер ESP 260 МБ')
t('VMD' in ins, 'в installation/ описана особенность Intel VMD')
t('parent' in ins, 'в installation/ описано правило parent у Ventoy')
t('audit mode' in ins.lower(), 'в installation/ зафиксирован отказ от audit mode')
ac = io.open(f'{OS}/activation/README.md', encoding='utf-8').read()
t('slmgr' in ac, 'в activation/ описан slmgr')
t('активатор' in ac.lower(), 'в activation/ зафиксирован отказ от активаторов')

print('\n[7] Скрипты на этом этапе не пишутся — решение заказчика')
stray = []
for root, dirs, files in os.walk(OS):
    for f in files:
        if f.endswith(('.ps1', '.sh')):
            stray.append(os.path.join(root, f))
t(not stray, f'в os/windows нет .ps1/.sh (решение: скрипты на Этапе 5)' + (f' -> {stray}' if stray else ''))

print('\n[8] Регрессия: предыдущие этапы целы')
for p in ['tools/rescue/README.md',
          'tools/rescue/data_recovery/DMDE/README.md',
          'tools/rescue/password/NTPWEdit/README.md',
          'tools/diagnostics/strelec-tools.md',
          'tools/backup/initial_backup/scripts/verify-backup.sh',
          'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md',
          'research/08-settings-attack-vectors.md',
          'ventoy-partition/ISO/windows/en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd.iso.md',
          'ventoy-partition/ISO/windows/ru-ru_windows_10_pro_x64.iso.md']:
    t(os.path.isfile(p), f'на месте {p}')
for n in ['smartmontools', 'CrystalDiskInfo', 'MemTest86Plus', 'Prime95',
          'stress-ng', 'DMDE', 'NTPWEdit',
          'en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd', 'ru-ru_windows_10_pro_x64']:
    t(n in names, f'в manifest осталась сущность {n}')

print('\n[9] Строка группы os/ в tools/README.md приведена к факту')
tr = io.open('tools/README.md', encoding='utf-8').read()
line = [l for l in tr.splitlines() if l.startswith('| `os/`')]
t(len(line) == 1, 'в tools/README.md одна строка для группы os/')
if line:
    for s in SUBS:
        t(s in line[0], f'в строке os/ названа подкатегория {s}')
    t('✅' in line[0], 'группа os/ отмечена как выполненная')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
