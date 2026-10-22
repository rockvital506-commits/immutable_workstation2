Это DiskPart скрипты, для быстрой разметки диска, для установки OS программой WinNTSetup, как в BIOS так и в UEFI.

Внимание:
Если вы не знаете что это, и как это работает, не пользультесь этим.
Я не несу ответственности за ваши неправильные действия.

При разметке диска, все данные с данного диска удаляются.

Для того чтобы выбрать нужный вам диск для разметки, выполните скрипт List_Disk.dps
Он полностью безопасный, выполняется команда - list disk


В скриптах для безопасности вместо номера диска прописана буква х
Замените в скрипте букву х, на номер диска который будет переразбит

в самой первой строке

select disk х

вместо буквы х введите номер нужного вам диска, например 

select disk 0

Редактировать скрипты можно в блокноте. Правой кнопкой мышки - Изменить

Если на требуемом диске имеются разделы, то лучше сначала удалить все разделы любой программой,
и вновь перезагрузиться в WinPE, и применить скрипт. Это предотвратит возможный конфликт назначения букв дисков.

Краткое описание скриптов:

UEFI_with_WindowsRE_and_Recovery_image_partition.dps
создаются разделы:
Windows RE tools partition
System boot partition
Microsoft Reserved (MSR) partition
Windows partition
Recovery image partition

UEFI_with_WinRE_ang_Boot_partition.dps
создаются разделы:
Windows RE tools partition
System boot partition
Microsoft Reserved (MSR) partition
Windows partition

UEFI_only_Boot_partition.dps
создаются разделы:
System boot partition
Microsoft Reserved (MSR) partition
Windows partition


BIOS_with_WindowsRE_Partition.dps
создаются разделы:
Windows RE tools partition
System boot partition
Windows partition

BIOS_no_WindowsRE_Partition.dps
создаются разделы:
System boot partition
Windows partition




