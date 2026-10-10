# updates/ — управление Центром обновления

Решение заказчика от 2026-10-07: **Windows Update не отключается**, а канал
сужается, плюс временная пауза на период обкатки настроек.

Основание — `research/08-settings-attack-vectors.md`, A1 и R3. Обновления
безопасности остаются: станция без них уязвимее, чем станция с телеметрией, а
требование проекта «`AllowTelemetry = 0` + обязательный пост-тест Центра
обновления» при полном отключении теряет смысл.

## Что закрываем и что оставляем

| Класс обновлений | Решение | Механизм |
|------------------|---------|----------|
| Обновления безопасности | **оставить** | — |
| Драйверы | **закрыть** | Политика `ExcludeWUDriversInQualityUpdate` + два ключа сообщества |
| Функциональные обновления | **закрепить версию** | `TargetReleaseVersion` |
| Получение обновлений «как можно скорее» | **выключить** | `IsContinuousInnovationOptedIn = 0` |
| Автоматическая перезагрузка | **выключить** | `NoAutoRebootWithLoggedOnUsers = 1` |
| Потребительские компоненты | **выключить** | `DisableWindowsConsumerFeatures` |
| Автоустановка приложений из Store | **выключить** | Отдельный ключ, см. ниже |
| Пауза на период обкатки | **временно** | `PauseQualityUpdates` / `PauseFeatureUpdates` |

## Блокировка драйверов

### Подтверждено первоисточником

`ExcludeWUDriversInQualityUpdate` описан в официальной документации Policy CSP —
Update:

| Поле | Значение |
|------|----------|
| Область | Device |
| Поддерживаемые редакции | Pro, Enterprise, Education, **IoT Enterprise / IoT Enterprise LTSC** |
| ОС | Windows 10 1607 (10.0.14393) и новее |
| Имя в GPO | «Do not include drivers with Windows Updates» |
| Путь в GPO | `Computer Configuration → Windows Components → Windows Update → Manage updates offered from Windows Update` |
| Ветка реестра | `Software\Policies\Microsoft\Windows\WindowsUpdate` |
| Имя параметра | `ExcludeWUDriversInQualityUpdate` |
| Значения | `0` — разрешить (по умолчанию), `1` — исключить |
| ADMX | `WindowsUpdate.admx` |
| Путь CSP | `./Device/Vendor/MSFT/Policy/Config/Update/ExcludeWUDriversInQualityUpdate` |

```cmd
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate /t REG_DWORD /d 1 /f
```

### Не является документированной политикой

Два ключа ниже широко применяются сообществом вместе с политикой, потому что
одной её бывает недостаточно. **В документации Microsoft их нет** — это
эмпирические значения, и на другой сборке они могут вести себя иначе.

| Ключ | Значение | Статус |
|------|----------|--------|
| `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching` → `SearchOrderConfig` | `0` | Ключ сообщества. Встречаются и значения `1`, `3` — расхождение в источниках |
| `HKLM\SOFTWARE\Microsoft\WindowsUpdate\UpdatePolicy\PolicyState` → `ExcludeWUDrivers` | `1` | Ключ состояния, а не политики. Система может переписать его сама |

Известный побочный эффект: Центр обновления начинает показывать сообщение о
включённой политике драйверов, даже если она снята. Лечится переводом политики
в `Enabled`, затем обратно в `Not Configured`.

### Точечно по устройству

Если блокировать все драйверы нельзя, а конфликтует одно устройство:

- `wushowhide.diagcab` — скрыть конкретное обновление;
- блокировка по Hardware ID через `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\DeviceSetup\Settings`.

## Закрепление версии и пауза

В Policy CSP — Update перечислены механизмы: `TargetReleaseVersion`,
`ProductVersion`, `PauseFeatureUpdates`, `PauseQualityUpdates`,
`PauseFeatureUpdatesStartTime`, `PauseQualityUpdatesStartTime`,
`ManagePreviewBuilds`.

Точные имена параметров реестра и допустимые значения для этих политик **не
сверены** с официальной страницей групповых политик — сверить через
`gpresult` после применения или по справке ADMX на станции.

Смысл для нашей задачи: закрепить станцию на 24H2, чтобы функциональное
обновление не приехало само, и снять паузу после того, как настройки проверены.

## Что уже делает Win11Debloat

Проверено по исходникам релиза `2026.08.24`, а не по описанию:

| Параметр | Ключ реестра | Что делает |
|----------|--------------|------------|
| `-DisableUpdateASAP` | `HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings` → `IsContinuousInnovationOptedIn = 0` | Выключает «Получать последние обновления, как только они будут доступны». Неблокирующие обновления всё равно придут, но позже |
| `-PreventUpdateAutoReboot` | `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU` → `NoAutoRebootWithLoggedOnUsers = 1` | Запрещает автоматическую перезагрузку при вошедшем пользователе |

Оба имеют файл отката: `Enable_Update_ASAP.reg` и `Allow_Auto_Reboot.reg`.

**Блокировки драйверов в Win11Debloat нет** — проверено поиском по `Scripts/`
и `Regfiles/`. Её закрывает режим `security` у WinUtil, см. ниже.

## Что делает WinUtil

Проверено по исходникам релиза `26.10.07`. Три режима вкладки `Updates`:
`Invoke-WPFUpdatesdefault.ps1`, `Invoke-WPFUpdatessecurity.ps1`,
`Invoke-WPFUpdatesdisable.ps1`. Режим `disable` **не применять** — он
противоречит решению R3.

Режим **`security`** закрывает почти весь объём R3 сам. Что он делает по коду:

| Действие | Ключ | Значение |
|----------|------|----------|
| Блокировка драйверов из WU | `Policies\Microsoft\Windows\WindowsUpdate` → `ExcludeWUDriversInQualityUpdate` | `1` |
| Отсрочка функциональных обновлений | `DeferFeatureUpdates` + `DeferFeatureUpdatesPeriodInDays` | `1` и `365` |
| Отсрочка качественных обновлений | `DeferQualityUpdates` + `DeferQualityUpdatesPeriodInDays` | `1` и `4` |
| Загрузка с уведомлением | `...\WindowsUpdate\AU` → `AUOptions` | `3` |
| Питание не управляет установкой | `...\WindowsUpdate\AU` → `AUPowerManagement` | `0` |
| Поиск драйверов в сети | `Policies\Microsoft\Windows\DriverSearching` → `DontSearchWindowsUpdate`, `DontPromptForWindowsUpdate` | `1` |
| Мастер драйверов | там же → `DriverUpdateWizardWuSearchEnabled` | `0` |
| Метаданные устройств из сети | `Policies\Microsoft\Windows\Device Metadata` → `PreventDeviceMetadataFromNetwork` | `1` |

Перед применением режим **возвращает работоспособность** Центра обновления:
`BITS` и `wuauserv` в `Manual`, `UsoSvc` в `Automatic` с запуском, включаются
задачи в `\Microsoft\Windows\UpdateOrchestrator`, `InstallService`,
`UpdateAssistant`, `WaaSMedic`, `WindowsUpdate`, снимается `NoAutoUpdate` и
`DODownloadMode`.

### Конфликт с Win11Debloat

> Режим `security` **удаляет** `NoAutoRebootWithLoggedOnUsers` из
> `...\WindowsUpdate\AU`. Win11Debloat с параметром `-PreventUpdateAutoReboot`
> этот ключ **выставляет**. Применение в порядке Win11Debloat → WinUtil
> отменяет запрет автоматической перезагрузки.

Порядок применения из индекса группы этот конфликт учитывает: WinUtil
запускается после Win11Debloat, и если запрет перезагрузки нужен, он
выставляется **после** WinUtil. Проверять значение ключа в пост-тесте.


## Пост-тест Центра обновления

Обязателен по требованию проекта. Проводится после применения телеметрических
правок и после перезагрузки.

| Проверка | Команда | Норма |
|----------|---------|-------|
| Служба работает | `Get-Service wuauserv` | `Running` или `Manual`, не `Disabled` |
| Оркестратор | `Get-Service UsoSvc` | Не `Disabled` |
| Поиск обновлений | Параметры → Центр обновления → «Проверить наличие обновлений» | Поиск проходит, ошибок сети нет |
| Политика драйверов | `reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate` | `0x1` |
| Версия закреплена | `gpresult /h report.html` | Политика видна в отчёте |
| Телеметрия | `reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry` | `0x0` |
| Перезагрузка не автоматическая | `reg query "...\WindowsUpdate\AU" /v NoAutoRebootWithLoggedOnUsers` | `0x1` |

Если поиск обновлений завершается ошибкой — телеметрические правки задели
Центр обновления. Откатывать по группе правок, начиная с последней, а не
сбрасывать всё сразу.

## Снятие паузы

Пауза ставится на период обкатки и **снимается после проверки**. Порядок:

1. Пост-тест Центра обновления пройден.
2. Настройки переживают перезагрузку — проверено дважды.
3. Эталонный бэкап образа снят.
4. Пауза снимается, обновления безопасности идут.

Станция, оставленная на паузе без срока, через несколько месяцев получает
набор обновлений одним пакетом — и часть настроек откатывается разом.

## Векторы отмены

Полный перечень — `research/08-settings-attack-vectors.md`. По этой
подкатегории критичны:

- **A1** — обновления возвращают параметры к значениям по умолчанию;
- **A2** — удаление `C:\Windows\System32\GroupPolicy` снимает все локальные
  политики, включая блокировку драйверов;
- **A8** — драйверы из WU могут понизить версию установленного драйвера;
- **A11** — загрузка с внешнего носителя обходит любые ACL.

## Не проверено на месте

| Пункт | Что нужно |
|-------|-----------|
| Имена параметров реестра для `TargetReleaseVersion` и паузы | Сверить с ADMX на станции |
| Достаточно ли одной политики без ключей сообщества | Прогон на тестовой машине |
| Поведение `PolicyState\ExcludeWUDrivers` после перезагрузки | Наблюдение на тестовой машине |
| Совместимость с IoT Enterprise LTSC 2024 | Прогон на станции |
