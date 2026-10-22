



set disk=C:\

reg load HKLM\WIM_Software %disk%Windows\System32\config\Software
reg load HKLM\WIM_Default %disk%Users\Default\NTUSER.DAT

Reg Add "HKLM\WIM_Default\Software\Microsoft\Office\16.0\Outlook\Options\General" /v "HideNewOutlookToggle" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Default\Software\Policies\Microsoft\Office\16.0\Outlook\Preferences" /v "NewOutlookMigrationUserSetting" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Software\Microsoft\WindowsUpdate\Orchestrator\UScheduler_Oobe\OutlookUpdate" /v "BlockedOobeUpdaters" /t REG_SZ /d "[\"MS_Outlook\"]" /f

reg unload HKLM\WIM_Software
reg unload HKLM\WIM_Default

DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.log*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.blf*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.regtrans-ms*"
DEL /F /S /Q /A:h "%disk%Windows\System32\SMI\Store\Machine\*.log*"
DEL /F /S /Q /A:h "%disk%Users\Default\*.log*"

pause
