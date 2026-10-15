# -*- coding: utf-8 -*-
"""Проверки группы tools/security/ (Этап 4.5)."""
import csv, io, os, re, sys
from baseline import expected

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # копия репозитория тестирует копию, не оригинал
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


SEC = 'tools/security'
SUBS = ['scanner', 'audit', 'encryption']
UTILS = {
    'Autoruns':        ('audit',      'Autoruns.zip.md'),
    'ProcessExplorer': ('audit',      'ProcessExplorer.zip.md'),
    'TCPView':         ('audit',      'TCPView.zip.md'),
    'VeraCrypt':       ('encryption', 'VeraCrypt_Setup_x64_1.26.29.msi.md'),
}
REQ = ['## Назначение', '## Когда применять', '## Состав каталога', '## Запуск',
       '## Ключи и типовые сценарии', '## Результаты и как их читать',
       '## Риски и предупреждения', '## Версия и источник', '## Аналоги',
       '## История изменений']

print('[1] Структура группы')
t(os.path.isfile(f'{SEC}/README.md'), 'есть индекс группы')
for s in SUBS:
    t(os.path.isdir(f'{SEC}/{s}'), f'есть подкатегория {s}/')
    t(os.path.isfile(f'{SEC}/{s}/README.md'), f'есть индекс {s}/README.md')
for name, (sub, stub) in UTILS.items():
    d = f'{SEC}/{sub}/{name}'
    t(os.path.isdir(d), f'есть каталог утилиты {d}')
    t(os.path.isfile(f'{d}/README.md'), f'есть {d}/README.md')
    t(os.path.isfile(f'{d}/{stub}'), f'есть заглушка {d}/{stub}')

print('\n[2] README утилит заполнены по шаблону')
for name, (sub, stub) in UTILS.items():
    s = io.open(f'{SEC}/{sub}/{name}/README.md', encoding='utf-8').read()
    missing = [r for r in REQ if r not in s]
    t(not missing, f'{name}: все обязательные разделы' + (f' (нет: {missing})' if missing else ''))
    probe = re.sub(r'https?://\S+', '', s)
    found = [m for m in re.findall(r'<([^<>\n]{1,40})>', probe) if m.strip() and ' ' not in m]
    t(not found, f'{name}: нет незаполненных плейсхолдеров' + (f' -> {found}' if found else ''))
    t('SHA256' in s, f'{name}: есть строка SHA256')
    t('История изменений' in s, f'{name}: есть история изменений')

print('\n[3] Честность по лицензиям и первоисточнику')
for name, (sub, _stub) in UTILS.items():
    s = io.open(f'{SEC}/{sub}/{name}/README.md', encoding='utf-8').read()
    low = s.lower()
    if name in ('Autoruns', 'ProcessExplorer', 'TCPView'):
        t('не сверена' in s, f'{name}: версия помечена несверенной')
        t('бизнес' in low or 'коммерческ' in low,
          f'{name}: лицензия разобрана применительно к коммерческому использованию')
        t('брендировани' in s, f'{name}: указано ограничение на снятие брендирования')
    if name == 'VeraCrypt':
        t('сверена с первоисточником' in low, 'VeraCrypt: версия сверена с первоисточником')
        t('52 789 248' in s, 'VeraCrypt: размер из API GitHub указан')
        t('коммерческое использование разрешено' in low,
          'VeraCrypt: коммерческое использование разрешено явно')
        t('CVE-2026-54073' in s, 'VeraCrypt: упомянута причина брать 1.26.29')

print('\n[4] Решения заказчика отражены в документах')
sc = io.open(f'{SEC}/scanner/README.md', encoding='utf-8').read()
t('Утилит здесь нет намеренно' in sc, 'в scanner/ объяснено отсутствие утилит')
t('MpCmdRun.exe' in sc, 'в scanner/ Defender описан средствами ОС')
t('Get-MpComputerStatus' in sc, 'в scanner/ есть способ посмотреть состояние Defender')
t('Start-MpWDOScan' in sc, 'в scanner/ описана офлайн-проверка')
t('10 дней' in sc, 'в scanner/ зафиксировано, что MSERT истекает')
t('соглас' in sc, 'в scanner/ есть условие про согласие заказчика')
for u in ['Dr.Web CureIt', 'Kaspersky Virus Removal Tool', 'SmartFix',
          'Emsisoft Emergency Kit', 'Microsoft Safety Scanner']:
    t(u in sc, f'в scanner/ назван сторонний сканер: {u}')
t('351' in sc and '702,77' in sc, 'в scanner/ приведена цена коммерческой лицензии CureIt!')
t('не подтверждена первоисточником' in sc,
  'в scanner/ прямо сказано, что лицензии сканеров не подтверждены')
grp = io.open(f'{SEC}/README.md', encoding='utf-8').read()
t('лицензионное' in grp, 'в индексе группы названо главное ограничение')
t('Defender' in grp, 'в индексе группы Defender обозначен как основной слой')
aud = io.open(f'{SEC}/audit/README.md', encoding='utf-8').read()
t('Autorunsc' in aud, 'в audit/ описан вывод в файл через Autorunsc')
t('-accepteula' in aud, 'в audit/ упомянут обязательный ключ -accepteula')
enc = io.open(f'{SEC}/encryption/README.md', encoding='utf-8').read()
t('BitLocker' in enc, 'в encryption/ BitLocker разобран как штатное средство')
t('manage-bde' in enc, 'в encryption/ приведены команды BitLocker')
t('приостанавл' in enc.lower(),
  'в encryption/ упомянута приостановка BitLocker перед снятием образа')

print('\n[5] Заглушки')
for name, (sub, stub) in UTILS.items():
    s = io.open(f'{SEC}/{sub}/{name}/{stub}', encoding='utf-8').read()
    t('CONVENTIONS' in s, f'{name}: ссылка на CONVENTIONS.md')
    t('PENDING' in s, f'{name}: SHA256 помечен PENDING')
    t('Как получить' in s, f'{name}: есть раздел «Как получить»')
    t('Куда положить на флешке' in s, f'{name}: есть раздел про размещение')
    bad_paths = [l for l in s.splitlines()
                 if ('E:\\' in l or 'Tools:\\' in l) and re.search(r'\\[a-z]+/[a-z]', l)]
    t(not bad_paths, f'{name}: нет смешанных разделителей в Windows-путях'
        + (f' -> {bad_paths}' if bad_paths else ''))

print('\n[6] manifest.csv')
raw = open('manifest.csv', 'rb').read()
t(b'\r\n' not in raw, 'manifest.csv в LF, без CRLF')
rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
head, body = rows[0], rows[1:]
t(len(body) == expected('manifest_rows'),
  f"строк данных {expected('manifest_rows')} (факт {len(body)})")
names = [r[2] for r in body]
t(len(set(names)) == len(names), 'нет дублей имён')
t(all(len(r) == 10 for r in body), 'во всех строках 10 полей')
t(not [r for r in body if r[0] == 'module' and r[2] == 'scanner'],
  'у пустой подкатегории scanner/ нет строки module — считать SELF-HASH не из чего')
by = {r[2]: r for r in body}
for name, (sub, stub) in UTILS.items():
    r = by.get(name)
    t(r is not None, f'{name}: есть строка в manifest.csv')
    if not r:
        continue
    t(r[0] == 'tool', f'{name}: type=tool')
    t(r[1] == f'security/{sub}', f'{name}: category=security/{sub}')
    t(r[3] == stub[:-3], f'{name}: file совпадает с заглушкой')
    t(r[4].startswith('https://'), f'{name}: url заполнен')
    t(r[9] == 'planned', f'{name}: status=planned')
t(by['VeraCrypt'][6] == '0' and by['VeraCrypt'][7] == '1.26.29',
  'VeraCrypt: версия 1.26.29 в манифесте')

print('\n[7] Скрипты на этом этапе не пишутся')
stray = []
for root, dirs, files in os.walk(SEC):
    for f in files:
        if f.endswith(('.ps1', '.sh')):
            stray.append(os.path.join(root, f))
t(not stray, 'в security/ нет .ps1/.sh' + (f' -> {stray}' if stray else ''))

print('\n[8] Регрессия: предыдущие этапы целы')
for p in ['tools/network/README.md',
          'tools/network/remote/RustDesk/README.md',
          'tools/os/windows/README.md',
          'tools/backup/initial_backup/scripts/backup-vscode.sh',
          'tests/test_rules.py',
          'research/10-security-scanners-audit-encryption.md',
          'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md']:
    t(os.path.isfile(p), f'на месте {p}')
for n in ['WinUtil', 'RustDesk', 'Nmap', 'Wireshark', 'DMDE', 'MemTest86Plus']:
    t(n in names, f'в manifest осталась сущность {n}')

print('\n[9] Строка группы security/ в tools/README.md приведена к факту')
tr = io.open('tools/README.md', encoding='utf-8').read()
line = [l for l in tr.splitlines() if l.startswith('| `security/`')]
t(len(line) == 1, 'в tools/README.md одна строка для группы security/')
if line:
    for s in SUBS:
        t(s in line[0], f'в строке security/ названа подкатегория {s}')
    t('✅' in line[0], 'группа security/ отмечена как выполненная')
    for old in ['antivirus/', 'crypto/', 'firmware-scan/']:
        t(old not in line[0], f'в строке нет прежней подкатегории {old}')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
