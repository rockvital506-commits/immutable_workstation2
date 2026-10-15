# Базовая настройка станции

**Шаг 8 станционного алгоритма.** Выполняется после установки LTSC и драйверов,
**до** блокировки телеметрии и **при отключённой сети**.

Порядок инструментов утверждён: **WinUtil → Win11Debloat → Sophia Script
точечно → свои скрипты**. Менять порядок нельзя: позже будет показано, что от
него зависит одно конкретное значение реестра.

## Перед началом

| Условие | Проверка |
|---------|----------|
| Драйверы установлены | `pnputil /enum-devices /problem` — 0 проблемных |
| Сеть физически отключена | Шаг 3 алгоритма; Wi-Fi выключен в BIOS |
| Снят дамп состояния | [`../../../tools/scripts/system-audit.ps1`](../../../tools/scripts/system-audit.ps1) `-OutDir <каталог>` |
| PowerShell от администратора | `whoami /groups` содержит SID `S-1-5-32-544` |

**Дамп обязателен до первого изменения.** Снятый после — для отката бесполезен:
исходные значения взять больше неоткуда.

## Шаг 1. Точка восстановления и экспорт политик

```powershell
Checkpoint-Computer -Description "Before base setup" -RestorePointType MODIFY_SETTINGS
reg export HKLM\SOFTWARE\Policies\Microsoft\Windows E:\reports\policies-before.reg
```

`reg export` — это откат шага 8 целиком. Если каталог политик не существует,
экспорт вернёт ошибку: это значит, что политик ещё нет, и откатывать нечего.

## Шаг 2. WinUtil

Утилита — [`../../os/windows/tweaks/WinUtil/`](../../os/windows/tweaks/WinUtil/).

Запуск из PowerShell от администратора, раздел **Tweaks**. Применять выборочно:
WinUtil содержит десятки переключателей, и часть из них ломает нужное
(например, отключение служб, от которых зависит печать или сеть).

**Обязательно:** раздел Updates security — он задаёт сужение канала обновлений
(`ExcludeWUDriversInQualityUpdate`, `DeferFeatureUpdates`, `DeferQualityUpdates`,
`AUOptions`) вместо полной блокировки.

## Шаг 3. Win11Debloat

Утилита — [`../../os/windows/debloat/Win11Debloat/`](../../os/windows/debloat/Win11Debloat/).

```powershell
.\Win11Debloat.ps1 -Silent -RunDefaults -CreateRestorePoint -LogPath E:\reports\win11debloat.log
```

Win11Debloat применяет локальные GPO, поэтому после него в `gpresult` и в
параметрах Windows появится «Управляется вашей организацией». Это ожидаемо и
не является неисправностью.

## Шаг 4. Ключ после WinUtil — порядок обязателен

`Invoke-WPFUpdatessecurity.ps1` из WinUtil **удаляет** значение
`NoAutoRebootWithLoggedOnUsers`. Если выставить его до WinUtil, оно будет
стёрто, и проверка в шаге 12 покажет расхождение, которого не было.

```powershell
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU' `
    -Name NoAutoRebootWithLoggedOnUsers -Value 1 -Type DWord
```

Поэтому: **WinUtil → Win11Debloat → этот ключ**. Не раньше.

## Шаг 5. Sophia Script точечно

Утилита — [`../../os/windows/gpo_lock/Sophia_Script/`](../../os/windows/gpo_lock/Sophia_Script/).

«Точечно» означает вызов отдельных функций, а не прогон всего сценария: у
Sophia 110 функций, и значительная часть относится к внешнему виду и
персонализации, которые на рабочей станции не нужны. Отбираются функции с
парным откатом — у Sophia каждая функция имеет обратную, и это единственный из
трёх инструментов, где откат предусмотрен самой утилитой.

## Шаг 6. Фиксация применённого

```powershell
reg export HKLM\SOFTWARE\Policies\Microsoft\Windows E:\reports\policies-after.reg
& E:\tools\scripts\system-audit.ps1 -OutDir E:\reports
& E:\tools\scripts\system-audit.ps1 -OutDir E:\reports -Diff E:\reports\<дамп из шага «Перед началом»>
```

Второй запуск с `-Diff` показывает, что именно изменилось. Код возврата `4` —
«найдены отклонения» — здесь **норма**: изменения планировались. Важно, чтобы в
списке не оказалось того, чего вы не применяли.

## Проверка

| Что | Команда | Норма |
|-----|---------|-------|
| Политики экспортированы | `Test-Path E:\reports\policies-before.reg` | True |
| Точка восстановления есть | `Get-ComputerRestorePoint` | запись существует |
| Ключ пережил WinUtil | `(Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU').NoAutoRebootWithLoggedOnUsers` | 1 |
| Что изменилось | `system-audit.ps1 -Diff <дамп>` | только применённое вами |

## Откат

Автоматически не откатывается. Последовательность:

1. `reg import E:\reports\policies-before.reg` — политики к состоянию до шага 8;
2. точечные значения — по дампу `system-audit` и обратным командам из вывода;
3. удалённые приложения **копией реестра не возвращаются**: только Store или
   `winget`. Это известное ограничение Win11Debloat, а не дефект применения;
4. крайний случай — `Restore-Computer -RestorePoint <номер>`.

## Не проверено на месте

| Пункт | Что нужно |
|-------|-----------|
| Параметры Win11Debloat для релиза 2026.08.24 | Прогон на станции; состав флагов меняется между релизами |
| Поведение `Checkpoint-Computer` на IoT Enterprise LTSC 2024 | Точка восстановления может быть отключена в редакции |
| Факт удаления `NoAutoRebootWithLoggedOnUsers` в WinUtil 26.10.07 | Проверить после применения, а не полагаться на прочитанный исходник |
| Наличие `gpresult` в LTSC | Утилита может отсутствовать в урезанных редакциях |
| Все три утилиты на флешке — заглушки | Реальных файлов нет, процедура не прогонялась ни разу |
