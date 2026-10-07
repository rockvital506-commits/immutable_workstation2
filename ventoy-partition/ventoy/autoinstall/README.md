# autoinstall/ — шаблоны автоматической установки

Каталог плагина `auto_install` Ventoy. Ventoy подсовывает файл ответа
установщику Windows/Linux, **не изменяя ISO**.

## Привязка в ventoy.json

```json
"auto_install": [
    { "parent": "/ISO/windows",
      "template": "/ventoy/autoinstall/autounattend.xml" }
]
```

**Обязательные правила, выведенные из дефектов Ventoy:**

1. Использовать **только `parent`** (каталог). Сопоставление по `"image"`,
   включая маски вида `/ISO/windows/*.iso`, не срабатывает — меню выбора файла
   ответа не появляется.
2. **Не задавать `timeout`** в `auto_install`: при его наличии Ventoy переходит
   к файлу ответа без ожидания, а сам таймаут не отрабатывает. Выбор — вручную.
3. Файл ответа обязан называться `autounattend.xml` — иначе установщик Windows
   его не подхватит.
4. При загрузке Ventoy предложит пункт «boot with /ventoy/autoinstall/autounattend.xml»
   — его нужно выбрать явно. Обычная загрузка ISO остаётся доступной.

## Состав (заполняется на Этапе 5)

| Файл | Назначение |
|------|-----------|
| `autounattend.xml` | Базовый файл ответа: язык, разметка GPT (ESP/MSR/OS), пропуск требований TPM/SecureBoot/сети, локальная учётная запись |
| `autounattend-ltsc.xml` | Вариант под IoT LTSC: без потребительских компонентов |
| `diskpart-256gb.txt` | Эталонная разметка под накопитель 256 ГБ |
| `README.md` | Этот файл |

## Проверка

1. `F5 → Tools menu → Check plugin json configuration (ventoy.json)` — покажет,
   распознан ли блок `auto_install`.
2. Тестовый прогон в VM (UEFI и Legacy) до применения на станции заказчика.
3. Файл ответа держать в git — он текстовый и полностью воспроизводим.

## Ограничение

Плагин работает для Windows и части Linux-дистрибутивов (kickstart/preseed).
Для Linux Mint Live-загрузки не применяется — там используется `persistence`.
