# linuxmint-22.3-cinnamon_casper-rw_16GB.dat

> **Это заглушка.** Файл `.dat` в git не хранится.
> Создайте его командой `CreatePersistentImg.sh` или скачайте готовый
> и переименуйте — см. `README.md` в этом каталоге.

| Поле | Значение |
|------|----------|
| Имя файла | `linuxmint-22.3-cinnamon_casper-rw_16GB.dat` |
| Назначение | Персистентность Linux Mint 22.3 Cinnamon |
| Размер | 16384 МБ |
| ФС внутри | ext4 |
| Метка | `casper-rw` |
| SHA256 | `PENDING` — вычислить после создания |
| Источник | Создаётся локально: `sudo bash CreatePersistentImg.sh -s 16384 -t ext4 -l casper-rw` |
| Альтернативный источник | https://github.com/ventoy/backend/releases |
| Добавлено | 2026-10-07 |

## Команда создания

```bash
sudo bash CreatePersistentImg.sh -s 16384 -t ext4 -l casper-rw
mv persistence.dat linuxmint-22.3-cinnamon_casper-rw_16GB.dat
sync
sha256sum linuxmint-22.3-cinnamon_casper-rw_16GB.dat
```

## Проверка

```bash
sha256sum "/mnt/ventoy/ventoy/persistence/linuxmint-22.3-cinnamon_casper-rw_16GB.dat"
```

## Примечания

- Метка обязана быть `casper-rw` — иначе Mint не подхватит персистентность.
- После записи обязательно `sync`.
- Эталонную сжатую копию хранить вне флешки для быстрого сброса.
