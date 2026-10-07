# stress-ng-0.22.01.tar.gz — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).

| Поле | Значение |
|------|----------|
| Имя файла | `stress-ng-0.22.01.tar.gz` |
| Назначение | Управляемая нагрузка на CPU, кэш, память, ввод-вывод в Linux |
| Версия | 0.22.01 (2026-09-20) |
| Источник | https://github.com/ColinIanKing/stress-ng/releases |
| Прямая ссылка | https://github.com/ColinIanKing/stress-ng/archive/refs/tags/V0.22.01.tar.gz |
| SHA256 | `PENDING` |
| Размер | ≈ 8 МБ |
| Лицензия | GPL v2 |
| Статус | `planned` |

## Как получить

```bash
curl -LO https://github.com/ColinIanKing/stress-ng/archive/refs/tags/V0.22.01.tar.gz
```

## Сборка

```bash
tar xf V0.22.01.tar.gz
cd stress-ng-0.22.01
make -j"$(nproc)"
sudo make install          # или просто запускать ./stress-ng
```

Зависимости для сборки в Mint: `build-essential`, при желании `libaio-dev`,
`libattr1-dev`, `libcap-dev`, `zlib1g-dev` — утилита собирается и без них, но
часть стрессоров будет отключена.

## Проверка подлинности

Релизы на GitHub сопровождаются тегом и, для части версий, подписью. Основное —
скачивать именно из `github.com/ColinIanKing/stress-ng`, а не с зеркал.

## Куда положить на флешке

`Tools:\diagnostics\cpu\stress-ng\`

Архив нужен как офлайн-источник. Если Live Mint с persistence уже настроен,
удобнее держать там установленный пакет, а архив — как резерв на случай
отсутствия сети.
