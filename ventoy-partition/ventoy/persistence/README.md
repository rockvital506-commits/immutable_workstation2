# persistence/ — файлы персистентности Live-систем

Каталог плагина `persistence` Ventoy. Здесь лежат **файлы-бэкенды** (`.dat`) —
дисковые образы с меткой, внутрь которых Live-система пишет изменения.

## Что настроено

| Образ | Бэкенд | Размер | Метка |
|-------|--------|--------|-------|
| `/ISO/linux/linuxmint-22.3-cinnamon-64bit.iso` | `linuxmint-22.3-cinnamon_casper-rw_16GB.dat` | 16 ГБ | `casper-rw` |

Конфигурация привязки — в `/ventoy/ventoy.json`, блок `persistence`, и
дублируется в `image_conf.json` как эталон для сверки.

## Как создать бэкенд

В среде Linux (или в Linux Mint с самой флешки):

```bash
# из архива Ventoy
sudo bash CreatePersistentImg.sh -s 16384 -t ext4 -l casper-rw
mv persistence.dat linuxmint-22.3-cinnamon_casper-rw_16GB.dat
sync
```

Готовые файлы разных размеров: `github.com/ventoy/backend/releases`.

| Ключ | Значение |
|------|----------|
| `-s` | Размер в МБ |
| `-t` | ФС: `ext2/3/4`, `xfs` (по умолчанию `ext4`) |
| `-l` | Метка. **Для Ubuntu и Linux Mint — `casper-rw`** |
| `-c` | Создать внутри `persistence.conf` (нужно Debian/Kali/Clonezilla, не Mint) |

## Расширение без потери данных

```bash
sudo bash ExtendPersistentImg.sh linuxmint-22.3-cinnamon_casper-rw_16GB.dat 4096
sync
```

## Правила

1. Метка обязана соответствовать дистрибутиву, иначе персистентность молча не
   подхватится.
2. Файл-бэкенд должен лежать **на первом разделе** флешки (Ventoy), не на `Tools`.
3. После записи — `sync`: незаписанный буфер даёт «пустой» бэкенд.
4. `.dat` в git не попадает — только заглушка `*.dat.md`.
5. Держать эталонную копию сжатого бэкенда вне флешки: после сжатия он занимает
   единицы МБ и служит для быстрого сброса к чистому состоянию.

## Ограничение, которое надо помнить

Плагин `persistence` работает **только для Live-Linux**. Для WinPE и Windows
персистентности у Ventoy нет — там применяются другие механизмы
(см. `research/02-findings.md`, раздел B).
