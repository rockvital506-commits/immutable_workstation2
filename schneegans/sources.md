# Источники и границы исследования

Исследовано в сессии 2026-10-24; повторно проверены верх формы и GitHub HEAD.
Версия сайта и HEAD совпали: `27237f82e9a8498d9c5bab7d398dc34b7682a1e8`,
коммит 2026-10-11. Это снимок состояния, не обещание неизменности сервиса.

| ID | Первичный источник | Что подтверждает |
|---|---|---|
| S01 | [Форма](https://schneegans.de/windows/unattend-generator/) | Блоки, варианты и предупреждения; заявлены Windows 10/11, 24H2/25H2/26H2 |
| S02 | [Usage](https://schneegans.de/windows/unattend-generator/usage/) | Носители, OEM/драйверы, логи, кодировка, чувствительные файлы |
| S03 | [Samples](https://schneegans.de/windows/unattend-generator/samples/) | Каталог примеров для дальнейшего целевого исследования; примеры ещё не аудированы |
| S04 | [Репозиторий](https://github.com/cschneegans/unattend-generator) | Открытая библиотека; не доказательство, что весь веб-интерфейс доступен локально |
| S05 | [MIT](https://github.com/cschneegans/unattend-generator/blob/27237f82e9a8498d9c5bab7d398dc34b7682a1e8/LICENSE.txt) | Лицензия библиотеки, не Windows и не обещание пригодности |
| S06 | [Script.cs](https://github.com/cschneegans/unattend-generator/blob/27237f82e9a8498d9c5bab7d398dc34b7682a1e8/modifier/Script.cs) | System, DefaultUser, FirstLogon, UserOnce; типы сценариев |
| S07 | [Delete.cs](https://github.com/cschneegans/unattend-generator/blob/27237f82e9a8498d9c5bab7d398dc34b7682a1e8/modifier/Delete.cs) | Удаление заданных чувствительных файлов через FirstLogon и зависимость от входа администратора |
| S08 | [Microsoft: answer files](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/update-windows-settings-and-scripts-create-your-own-answer-file-sxs?view=windows-11) | Проходы Setup; DISM Apply-Unattend не проверяет всю установку |
| S09 | [Microsoft: keys](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/work-with-product-keys-and-activation-auth-phases?view=windows-11) | Различие выбора редакции и активации |
| S10 | [Ventoy AutoInstall](https://www.ventoy.net/en/plugin_autoinstall.html) | Привязка шаблонов к ISO; интеграцию проверять отдельно |

Не проводились: реальная генерация нашей конфигурации сайтом, полный аудит всех
ветвей кода, сетевой/приватностный аудит сервиса, испытание с LTSC на MSI.
Состав блоков записан по изученной форме; условные поля и точные значения
перепроверяются при разборе каждого блока. Не заявлять браузерную локальность
обработки. Не отправлять реальные секреты. Рекомендации агента в справочнике
отделены от утверждений автора ссылками и словами «рекомендация».
