# -*- coding: utf-8 -*-
"""Проверки группы tools/rescue/ (Этап 4.2)."""
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

RES = 'tools/rescue'
SUBS = ['password', 'data_recovery', 'partition', 'registry', 'boot']
UTILS = {
    'DMDE':     ('data_recovery', 'dmde-4-4-4-842-win64-gui.zip.md'),
    'NTPWEdit': ('password',      'ntpwed07.zip.md'),
}

print('[1] Структура группы')
t(os.path.isfile(f'{RES}/README.md'), 'есть индекс группы')
for s in SUBS:
    t(os.path.isdir(f'{RES}/{s}'), f'есть подкатегория {s}/')
    t(os.path.isfile(f'{RES}/{s}/README.md'), f'есть индекс {s}/README.md')
for name, (sub, stub) in UTILS.items():
    d = f'{RES}/{sub}/{name}'
    t(os.path.isdir(d), f'есть каталог утилиты {d}')
    t(os.path.isfile(f'{d}/README.md'), f'есть {d}/README.md')
    t(os.path.isfile(f'{d}/{stub}'), f'есть заглушка {d}/{stub}')

print('\n[2] README утилит заполнены по шаблону')
REQ = ['## Назначение', '## Когда применять', '## Состав каталога', '## Запуск',
       '## Ключи и типовые сценарии', '## Результаты и как их читать',
       '## Риски и предупреждения', '## Версия и источник', '## Аналоги',
       '## История изменений']
for name, (sub, stub) in UTILS.items():
    s = io.open(f'{RES}/{sub}/{name}/README.md', encoding='utf-8').read()
    missing = [r for r in REQ if r not in s]
    t(not missing, f'{name}: все обязательные разделы' + (f' (нет: {missing})' if missing else ''))
    probe = re.sub(r'https?://\S+', '', s)
    found = [m for m in re.findall(r'<([^<>\n]{1,40})>', probe) if ' ' not in m.strip() and m.strip()]
    t(not found, f'{name}: нет незаполненных плейсхолдеров' + (f' -> {found}' if found else ''))
    t('SHA256' in s, f'{name}: есть строка SHA256')
    t('не сверена с официальным сайтом' in s,
      f'{name}: честно помечено, что версия не сверена с первоисточником')

print('\n[3] Заглушки')
for name, (sub, stub) in UTILS.items():
    s = io.open(f'{RES}/{sub}/{name}/{stub}', encoding='utf-8').read()
    t('CONVENTIONS' in s, f'{name}: ссылка на CONVENTIONS.md')
    t('PENDING' in s, f'{name}: SHA256 помечен PENDING')

print('\n[4] manifest.csv')
raw = open('manifest.csv','rb').read()
t(b'\r\n' not in raw, 'manifest.csv в LF, без CRLF')
rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
head, body = rows[0], rows[1:]
# Этап 4.3 добавил 3 утилиты группы os/windows: было 21, стало 24
t(len(rows) - 1 == 24, f'24 строки данных (факт {len(rows)-1})')
names = [r[2] for r in body]
t(len(names) == len(set(names)), 'нет дублей имён')
t(all(len(r) == 10 for r in body), 'во всех строках 10 полей')
for name, (sub, stub) in UTILS.items():
    row = next((r for r in body if r[2] == name), None)
    t(row is not None, f'{name}: есть строка в manifest.csv')
    if row:
        t(row[0] == 'tool', f'{name}: type=tool')
        t(row[1] == f'rescue/{sub}', f'{name}: category=rescue/{sub}')
        t(row[3] == stub[:-3], f'{name}: file совпадает с заглушкой')
        t(row[4].startswith('http'), f'{name}: url заполнен')
        t(row[7] not in ('PENDING', '0', ''), f'{name}: version заполнена ({row[7]})')
        t(os.path.isdir('tools/' + row[1] + '/' + row[2]), f'{name}: каталог по category есть')

print('\n[5] Содержание: матрица решений и ограничения')
idx = io.open(f'{RES}/README.md', encoding='utf-8').read()
for needle in ['Reset Windows Password', 'R-Studio', 'EasyBCD', 'Registry Editor PE',
               'DMDE', 'NTPWEdit', 'Не писать на диск']:
    t(needle in idx, f'в индексе группы упомянут «{needle}»')
pw = io.open(f'{RES}/password/README.md', encoding='utf-8').read()
for needle in ['EFS', 'DPAPI', 'BitLocker', 'домен', 'Microsoft']:
    t(needle in pw, f'в password/ зафиксировано ограничение «{needle}»')
dr = io.open(f'{RES}/data_recovery/README.md', encoding='utf-8').read()
for needle in ['TRIM', 'HDD Regenerator', 'образ диска']:
    t(needle in dr, f'в data_recovery/ есть «{needle}»')
# «на другой носитель» записано с markdown-выделением, поэтому сверяем по словам
plain = re.sub(r'\*+', '', dr)
t('другой носитель' in plain and 'на исходный' in plain,
  'в data_recovery/ зафиксировано правило восстановления на другой носитель')
rg = io.open(f'{RES}/registry/README.md', encoding='utf-8').read()
for needle in ['reg load', 'reg unload', 'ControlSet001', 'NTUSER.DAT']:
    t(needle in rg, f'в registry/ есть «{needle}»')
bt = io.open(f'{RES}/boot/README.md', encoding='utf-8').read()
for needle in ['bcdboot', 'bootrec', 'EasyUEFI', 'VMD']:
    t(needle in bt, f'в boot/ есть «{needle}»')
pt = io.open(f'{RES}/partition/README.md', encoding='utf-8').read()
for needle in ['4096', 'mbr2gpt', '260']:
    t(needle in pt, f'в partition/ есть «{needle}»')

print('\n[6] Правило «не дублировать Strelec» соблюдено')
dups = [n for n in ['R-Studio', 'TestDisk', 'DiskGenius', 'EasyBCD', 'Kon-Boot',
                    'MiniTool', 'Acronis'] if os.path.isdir(f'{RES}') and
        any(os.path.isdir(os.path.join(RES, s, n)) for s in SUBS)]
t(not dups, f'на Tools не скопированы утилиты, уже лежащие в Strelec: {dups or "нет"}')
t(len(UTILS) == 2, f'портативных утилит ровно две (факт {len(UTILS)}) — только под сценарий живой ОС')

print('\n[7] Текст и ссылки по всему репозиторию')
CJK = re.compile('[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')
bad_cjk, broken = [], []
for root, dirs, files in os.walk('.'):
    if root.startswith('./.git'): continue
    for f in files:
        p = os.path.join(root, f)
        if f.endswith(('.md', '.sh', '.ps1', '.py', '.json', '.csv')):
            try: txt = io.open(p, encoding='utf-8').read()
            except Exception: continue
            if CJK.search(txt): bad_cjk.append(p)
        if f.endswith('.md'):
            txt = io.open(p, encoding='utf-8').read()
            for m in re.finditer(r'\]\(([^)]+)\)', txt):
                l = m.group(1).split('#')[0]
                if not l or l.startswith(('http://', 'https://', 'mailto:')): continue
                if not os.path.exists(os.path.normpath(os.path.join(root, l))):
                    broken.append(f'{p} -> {l}')
t(not bad_cjk, 'нет CJK-вкраплений' + (f': {bad_cjk}' if bad_cjk else ''))
t(not broken, 'нет битых относительных ссылок' + ('\n       ' + '\n       '.join(broken) if broken else ''))

print('\n[8] Регрессия: предыдущие этапы целы')
for p in ['tools/diagnostics/strelec-tools.md',
          'tools/diagnostics/cpu/Prime95/README.md',
          'tools/backup/initial_backup/scripts/verify-backup.sh',
          'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md',
          'ventoy-partition/builds/_templates/algorithm.md']:
    t(os.path.isfile(p), f'на месте {p}')
for n in ['smartmontools', 'CrystalDiskInfo', 'MemTest86Plus', 'Prime95', 'stress-ng']:
    t(n in names, f'в manifest осталась утилита {n}')
t('2026.02.05' in io.open('manifest.csv', encoding='utf-8').read(),
  'версия Strelec в manifest — 2026.02.05')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
