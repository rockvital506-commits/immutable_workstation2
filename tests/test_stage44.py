# -*- coding: utf-8 -*-
"""Проверки группы tools/network/ (Этап 4.4)."""
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

NET = 'tools/network'
SUBS = ['diagnostics', 'speed', 'scan', 'wifi', 'remote', 'capture']
UTILS = {
    'RustDesk':     ('remote',  'rustdesk-1.5.0-x86_64.exe.md',        '1.5.0'),
    'iperf3':       ('speed',   'iperf-3.22-win64.zip.md',             '3.22'),
    'Nmap':         ('scan',    'nmap-7.991-setup.exe.md',             '7.991'),
    'Wireshark':    ('capture', 'WiresharkPortable64_4.6.9.paf.exe.md','4.6.9'),
    'WifiInfoView': ('wifi',    'wifiinfoview-x64.zip.md',             '3.00'),
    'MyPublicWifi': ('wifi',    'MyPublicWiFi.exe.md',                 '31.3'),
}

print('[1] Структура группы')
t(os.path.isfile(f'{NET}/README.md'), 'есть индекс группы')
for s in SUBS:
    t(os.path.isdir(f'{NET}/{s}'), f'есть подкатегория {s}/')
    t(os.path.isfile(f'{NET}/{s}/README.md'), f'есть индекс {s}/README.md')
for name, (sub, stub, ver) in UTILS.items():
    d = f'{NET}/{sub}/{name}'
    t(os.path.isdir(d), f'есть каталог утилиты {d}')
    t(os.path.isfile(f'{d}/README.md'), f'есть {d}/README.md')
    t(os.path.isfile(f'{d}/{stub}'), f'есть заглушка {d}/{stub}')
t(os.path.isfile(f'{NET}/remote/RustDesk/LICENSE-SOURCE.md'),
  'есть LICENSE-SOURCE.md у RustDesk (требование AGPL)')

print('\n[2] README утилит заполнены по шаблону')
REQ = ['## Назначение', '## Когда применять', '## Состав каталога', '## Запуск',
       '## Ключи и типовые сценарии', '## Результаты и как их читать',
       '## Риски и предупреждения', '## Версия и источник', '## Аналоги',
       '## История изменений']
for name, (sub, stub, ver) in UTILS.items():
    s = io.open(f'{NET}/{sub}/{name}/README.md', encoding='utf-8').read()
    missing = [r for r in REQ if r not in s]
    t(not missing, f'{name}: все обязательные разделы' + (f' (нет: {missing})' if missing else ''))
    probe = re.sub(r'https?://\S+', '', s)
    found = [m for m in re.findall(r'<([^<>\n]{1,40})>', probe) if ' ' not in m.strip() and m.strip()]
    t(not found, f'{name}: нет незаполненных плейсхолдеров' + (f' -> {found}' if found else ''))
    t('SHA256' in s, f'{name}: есть строка SHA256')
    t(ver in s, f'{name}: указана версия {ver}')

print('\n[3] Честность по первоисточнику')
src = {
    'RustDesk':     'сверена с первоисточником',
    'iperf3':       'сверена с первоисточником',
    'Nmap':         'не сверена с первоисточником',
    'Wireshark':    'не сверена с первоисточником',
    'WifiInfoView': 'не сверена с первоисточником',
    'MyPublicWifi': 'не проверена с первоисточником',
}
for name, phrase in src.items():
    sub = UTILS[name][0]
    s = io.open(f'{NET}/{sub}/{name}/README.md', encoding='utf-8').read()
    t(phrase in s, f'{name}: статус сверки помечен («{phrase}»)')

print('\n[4] Заглушки')
for name, (sub, stub, ver) in UTILS.items():
    s = io.open(f'{NET}/{sub}/{name}/{stub}', encoding='utf-8').read()
    t('CONVENTIONS' in s, f'{name}: ссылка на CONVENTIONS.md')
    t('PENDING' in s, f'{name}: SHA256 помечен PENDING')
    t('Как получить' in s, f'{name}: есть раздел «Как получить»')
    t('Куда положить на флешке' in s, f'{name}: есть раздел про размещение')
    bad_paths = [l for l in s.splitlines()
                 if ('E:\\' in l or 'Tools:\\' in l) and re.search(r'\\[a-z]+/[a-z]', l)]
    t(not bad_paths, f'{name}: нет смешанных разделителей в Windows-путях'
        + (f' -> {bad_paths}' if bad_paths else ''))

print('\n[5] manifest.csv')
raw = open('manifest.csv', 'rb').read()
t(b'\r\n' not in raw, 'manifest.csv в LF, без CRLF')
rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
head, body = rows[0], rows[1:]
t(len(body) == 30, f'30 строк данных (факт {len(body)})')
names = [r[2] for r in body]
t(len(set(names)) == len(names), 'нет дублей имён')
t(all(len(r) == 10 for r in body), 'во всех строках 10 полей')
by = {r[2]: r for r in body}
for name, (sub, stub, ver) in UTILS.items():
    r = by.get(name)
    t(r is not None, f'{name}: есть строка в manifest.csv')
    if not r:
        continue
    t(r[0] == 'tool', f'{name}: type=tool')
    t(r[1] == f'network/{sub}', f'{name}: category=network/{sub}')
    t(r[3] == stub[:-3], f'{name}: file совпадает с заглушкой')
    t(r[4].startswith('https://'), f'{name}: url заполнен')
    t(r[7] == ver, f'{name}: version={ver}')
    t(r[9] == 'planned', f'{name}: status=planned')
    t(os.path.isfile(f'{NET}/{sub}/{name}/{r[3]}.md'), f'{name}: заглушка по file существует')

print('\n[6] Правило «не дублировать Strelec» соблюдено')
grp = io.open(f'{NET}/README.md', encoding='utf-8').read()
for u in ['TeamViewer', 'AnyDesk', 'Ammyy', 'Advanced IP Scanner', 'PENetwork',
          'UltraVNC', 'OpenVPN', 'PuTTY']:
    t(u in grp, f'в индексе группы названа утилита Strelec: {u}')
t('нет вообще' in grp, 'в индексе зафиксировано, каких ниш в Strelec нет')
t('iperf3' in grp and 'Nmap' in grp and 'Wireshark' in grp,
  'в индексе названы все три нишевые утилиты')

print('\n[7] Содержание подкатегорий')
d = io.open(f'{NET}/diagnostics/README.md', encoding='utf-8').read()
for cmd in ['ping', 'tracert', 'pathping', 'nslookup', 'Test-NetConnection',
            'ipconfig', 'netstat', 'arp -a', 'netsh']:
    t(cmd in d, f'в diagnostics/ есть {cmd}')
t('Утилит здесь **нет намеренно**' in d, 'в diagnostics/ объяснено отсутствие утилит')
sp = io.open(f'{NET}/speed/README.md', encoding='utf-8').read()
t('940' in sp, 'в speed/ есть ориентир для гигабита')
t('две стороны' in sp or 'двумя узлами' in sp, 'в speed/ указано, что нужны две стороны')
sc = io.open(f'{NET}/scan/README.md', encoding='utf-8').read()
t('разрешения владельца' in sc, 'в scan/ есть требование разрешения')
t('Advanced IP Scanner' in sc, 'в scan/ узлы отданы Advanced IP Scanner из Strelec')
w = io.open(f'{NET}/wifi/README.md', encoding='utf-8').read()
t('не запускается' in w, 'в wifi/ зафиксировано ограничение встроенного хот-спота')
t('1, 6, 11' in w, 'в wifi/ указаны неперекрывающиеся каналы 2.4 ГГц')
t('URL-журналирование' in w, 'в wifi/ упомянут запрет журналирования')
t('lan.rs' in w, 'в wifi/ описана связка с RustDesk')
r = io.open(f'{NET}/remote/README.md', encoding='utf-8').read()
t('--noinstall' in r, 'в remote/ описан портативный режим')
t('AGPL' in r, 'в remote/ названа лицензия')
t('lan.rs' in r, 'в remote/ упомянут LAN-режим без сервера')
t('несанкционированн' in r.lower() or 'Несеансовый доступ' in r,
  'в remote/ есть раздел про несеансовый доступ')
c = io.open(f'{NET}/capture/README.md', encoding='utf-8').read()
t('Npcap' in c, 'в capture/ объяснена роль Npcap')
t('портативная' in c.lower(), 'в capture/ объяснён выбор портативной сборки')
t('tcp.analysis.retransmission' in c, 'в capture/ есть фильтр повторных передач')

print('\n[7b] Правки после первого прогона (регрессия на найденные дефекты)')
# Д1: в групповом индексе было «четыре из шести сверены» и тут же перечислены
#     четыре несверенные — фраза противоречила сама себе.
g = io.open(f'{NET}/README.md', encoding='utf-8').read()
line = [l for l in g.splitlines() if 'из шести' in l]
t(len(line) == 1, 'в индексе группы ровно одна строка о доле сверенных версий')
if line:
    t('две из шести' in line[0], 'строка о доле сверенных версий корректна')
    t('четыре' not in line[0].lower(), 'в строке нет противоречащего числа')


def verified(name):
    """Сверена ли версия с первоисточником. Регистронезависимо, оба глагола:
    в MyPublicWifi статус написан и как «не проверена», и как «НЕ сверена»."""
    txt = io.open(f'{NET}/{UTILS[name][0]}/{name}/README.md', encoding='utf-8').read()
    low = txt.lower()
    neg = ('не сверена с первоисточником' in low
           or 'не проверена с первоисточником' in low)
    return 'сверена с первоисточником' in low and not neg


n_verified = sum(1 for n in UTILS if verified(n))
t(n_verified == 2, f'по факту с первоисточником сверено 2 утилиты (факт {n_verified})')

# Д2: диапазон портов 0-65535 — это 65536 значений, а не 65535.
nm = io.open(f'{NET}/scan/Nmap/README.md', encoding='utf-8').read()
t('65535 портов' not in nm, 'в Nmap нет неверного «65535 портов»')
t('65536 портов диапазона 0-65535' in nm, 'в Nmap корректно описан диапазон портов')

# Д3: порядок диагностики обрывался на шаге 6, индекс группы и PLAN говорят о 8.
steps = re.findall(r'^(\d)\. \*\*', d, re.M)
t(steps == ['1', '2', '3', '4', '5', '6', '7', '8'],
  'в diagnostics/ восемь шагов порядка' + (f' (факт {steps})' if len(steps) != 8 else ''))
for link in ['../speed/', '../scan/', '../wifi/', '../capture/']:
    t(f'[`{link}`]({link})' in d, f'шаги diagnostics/ ссылаются на {link}')
grp_steps = re.findall(r'^\d+\. ', grp, re.M)
t(len(grp_steps) >= 8, f'порядок в групповом индексе не короче diagnostics/ (факт {len(grp_steps)})')

# Д4: утверждение про Npcap в WinPE звучало безоговорочно, хотя вопрос открыт.
t('Работает из-под WinPE: **не проверено**' in nm,
  'в Nmap режим WinPE помечен непроверенным, а не утверждается')
t('TCP-connect может работать и без драйвера' in sc,
  'в scan/ тот же вопрос помечен в «Не проверено на месте»')

print('\n[8] Скрипты на этом этапе не пишутся')
stray = []
for root, dirs, files in os.walk(NET):
    for f in files:
        if f.endswith(('.ps1', '.sh')):
            stray.append(os.path.join(root, f))
t(not stray, f'в network/ нет .ps1/.sh' + (f' -> {stray}' if stray else ''))

print('\n[9] Регрессия: предыдущие этапы целы')
for p in ['tools/os/windows/README.md',
          'tools/os/windows/debloat/Win11Debloat/README.md',
          'tools/os/windows/tweaks/WinUtil/README.md',
          'tools/rescue/README.md',
          'tools/diagnostics/strelec-tools.md',
          'research/09-mypublicwifi-rustdesk.md',
          'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md']:
    t(os.path.isfile(p), f'на месте {p}')
for n in ['WinUtil', 'Win11Debloat', 'Sophia_Script', 'DMDE', 'NTPWEdit',
          'smartmontools', 'MemTest86Plus']:
    t(n in names, f'в manifest осталась сущность {n}')

print('\n[10] Строка группы network/ в tools/README.md приведена к факту')
tr = io.open('tools/README.md', encoding='utf-8').read()
line = [l for l in tr.splitlines() if l.startswith('| `network/`')]
t(len(line) == 1, 'в tools/README.md одна строка для группы network/')
if line:
    for s in SUBS:
        t(s in line[0], f'в строке network/ названа подкатегория {s}')
    t('✅' in line[0], 'группа network/ отмечена как выполненная')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
