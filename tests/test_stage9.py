# -*- coding: utf-8 -*-
"""Проверки Этапа 9 — обновление и целостность.

Решения владельца от 2026-10-15:
  1. Бэкап разделов — на внешний диск, хранится отдельно от флешки.
  2. Объём бэкапа — конфиг и builds/, не полные образы разделов.
  3. Сверка SHA256 — все типы сущностей, с путём по разделам.
  4. Периодичность — раз в месяц.

Расхождения, закрытые на этом этапе (research/19-update-integrity.md):
N1 сверялись только ISO; N2 путь строился без учёта раздела TOOLS;
N4 то же в .ps1; N5 регламента обновления не было; N7 бэкапа разделов не было;
N8 противоречие в назначении ventoy-partition/backup/.
"""
import io, os, re, sys

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


def read(p):
    return io.open(p, encoding='utf-8').read()


def flat(s):
    return re.sub(r'\s+', ' ', s)


# --- [1] Документы существуют ---------------------------------------------

print('\n[1] Документы обслуживания флешки')
for f in ['flash-update.md', 'flash-backup.md']:
    p = f'tools/docs/{f}'
    t(os.path.isfile(p), f'есть {p}')
    t(os.path.getsize(p) > 3000, f'{p} не пуст ({os.path.getsize(p)} байт)')

idx = read('tools/docs/README.md')
for f in ['flash-update.md', 'flash-backup.md']:
    t(f']({f})' in idx, f'индекс ссылается на {f}')
t('Обслуживание самой флешки' in idx,
  'в индексе есть раздел об обслуживании носителя')

# --- [2] Битые ссылки ------------------------------------------------------

print('\n[2] Относительные ссылки')
broken = 0
for f in ['README.md', 'flash-update.md', 'flash-backup.md']:
    md = f'tools/docs/{f}'
    src = re.sub(r'`[^`\n]*`', '', read(md))
    src = re.sub(r'```.*?```', '', src, flags=re.S)
    for m in re.finditer(r'\]\(([^)#]+)\)', src):
        link = m.group(1).split('#')[0]
        if not link or link.startswith(('http://', 'https://', 'mailto:')):
            continue
        if not os.path.exists(os.path.normpath(os.path.join('tools/docs', link))):
            bad(f'{md}: битая ссылка {link}')
            broken += 1
t(broken == 0, f'битых ссылок нет (найдено {broken})')

# --- [3] Регламент обновления ---------------------------------------------

print('\n[3] flash-update.md')
upd = flat(read('tools/docs/flash-update.md'))
t('Две разные процедуры' in upd,
  'обновление Ventoy отделено от обновления содержимого')
t('MBR' in upd and 'GPT' in upd and 'переустановка' in upd.lower(),
  'смена MBR/GPT названа случаем, требующим переустановки')
t('VentoyPlugson' in upd and '1.1.16' in upd,
  'оговорка про VentoyPlugson до 1.1.16 есть')
t('UEFI CA 2023' in upd, 'запись ключа при первой загрузке описана')
t('1.1.18' in upd and '1.1.14' in upd and '1.1.11' in upd,
  'версии: актуальная, минимум для флешки, минимум для файлов ответа')
t('Update' in upd and 'Install' in upd,
  'Update и Install различены')
t('не замена резервной копии' in upd or 'не замена' in upd,
  'оговорка, что сохранение файлов при Update — не замена бэкапа')
t('раз в месяц' in upd, 'периодичность указана')
for sec in ['Образы', 'Утилиты', 'Скрипты и конфиги']:
    t(sec in upd, f'раздел «{sec}» есть')
t('repo-validate' in upd and 'csv-check' in upd and 'check-flash' in upd,
  'порядок проверки после обновления указан')
t('не признак благополучия' in upd,
  'предупреждение о нуле сверенных сумм есть')
t('WIMBOOT' in upd, 'запасной режим загрузки назван')

# --- [4] Регламент бэкапа --------------------------------------------------

print('\n[4] flash-backup.md')
bku = read('tools/docs/flash-backup.md')
bkf = flat(bku)
t('Внешний диск' in bku or 'внешний диск' in bku,
  'место хранения — внешний диск')
t('не вместе с флешкой' in bkf,
  'сказано, что диск хранится отдельно от флешки')
t('Почему не полный образ разделов' in bku,
  'обоснование объёма бэкапа есть')
t('manifest.csv' in bku,
  'ссылка на манифест как источник для повторного скачивания')
t('17408' in bku, 'размер дампа GPT указан точно (34 x 512)')
for cmd in ['dd if=', 'lsblk', 'blockdev --getsz', 'count=34']:
    t(cmd in bku, f'команда {cmd.strip()} есть')
t('gpt-backup34' in bku, 'резервная GPT в конце диска тоже снимается')
t('ls -l' in bku, 'проверка дампа после снятия есть')
t('Раз в месяц' in bku or 'раз в месяц' in bkf, 'периодичность указана')
t('Клиентские данные сюда не кладутся никогда' in bku,
  'запрет хранения клиентских данных есть')
t('persistence' in bku, 'persistence рассмотрен отдельно')
t('Не проверено' in bku, 'раздел «Не проверено» есть')
t('не снят' in bkf,
  'честно сказано, что дамп на этой флешке ещё не снят')

# --- [5] Сверка сумм: все типы, путь по разделам --------------------------

print('\n[5] check-flash: сверка всех типов')
sh = read('scripts/check-flash.sh')
ps = read('scripts/check-flash.ps1')
t('[ "$mtype" = \'iso\' ] || continue' not in sh,
  '.sh: прежний фильтр только-ISO убран')
t("$row.type -ne 'iso' -or" not in ps,
  '.ps1: прежний фильтр только-ISO убран')
for name, src, mount in [('.sh', sh, 'TOOLS_MOUNT'), ('.ps1', ps, 'ToolsRoot')]:
    t(mount in src, f'{name}: раздел TOOLS участвует в сверке сумм')
    t('case "$mtype" in' in src or "row.type -eq 'iso'" in src,
      f'{name}: база пути выбирается по типу')
    t('Итог сверки сумм' in src, f'{name}: итог сверки выводится')
    t('ни одна контрольная сумма не была сверена с реальным файлом' in src,
      f'{name}: случай «сверять нечего» назван явно')
t('SHA256 образов и бинарников' in sh and 'SHA256 образов и бинарников' in ps,
  'заголовки обоих скриптов говорят про бинарники')

# --- [6] Противоречие о назначении backup/ закрыто ------------------------

print('\n[6] ventoy-partition/backup/')
tr = read('tools/README.md')
t('только вне флешки' in tr,
  'tools/README.md больше не предлагает хранить бэкапы клиентов на флешке')
t('только дампы первых секторов' in tr,
  'назначение каталога backup/ сформулировано')
t('Бэкапы клиентов и образы машин — только в `ventoy-partition/backup/`' not in tr,
  'прежней формулировки не осталось')
t(os.path.isfile('ventoy-partition/backup/.keep'),
  'каталог backup/ на месте')
t('flash-backup.md' in tr, 'tools/README.md ссылается на регламент бэкапа')

# --- [7] Валидация знает о новых документах -------------------------------

print('\n[7] repo-validate проверяет новые документы')
rv_sh = read('scripts/repo-validate.sh')
rv_ps = read('scripts/repo-validate.ps1')
for f in ['flash-update.md', 'flash-backup.md']:
    t(f'tools/docs/{f}' in rv_sh, f'repo-validate.sh проверяет {f}')
    t(f'tools/docs/{f}' in rv_ps, f'repo-validate.ps1 проверяет {f}')

# --- [8] Манифест учитывает каталог документации --------------------------

print('\n[8] manifest.csv')
cc = read('scripts/csv-check.py')
for f in ['flash-update.md', 'flash-backup.md']:
    t(f'"tools/docs/{f}"' in cc, f'SELF_ENTITIES["docs"] содержит {f}')
mf = read('manifest.csv')
t('module,docs,docs,' in mf, 'строка module,docs,docs на месте')

# --- [9] Регрессия --------------------------------------------------------

print('\n[9] Регрессия')
for p in ['research/19-update-integrity.md', 'scripts/check-flash.sh',
          'scripts/check-flash.ps1', 'tests/test_stage8.py',
          'tools/docs/compatibility.md']:
    t(os.path.isfile(p), f'на месте {p}')
t('Кто выбирает образ' in read('tools/docs/compatibility.md'),
  'раздел о выборе образа не потерян')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
