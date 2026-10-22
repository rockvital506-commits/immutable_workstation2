

::
:: Enable WinDefender  =============================================================================================================================
::

set disk=C:\

reg load HKLM\WIM_Software %disk%Windows\System32\config\Software
reg load HKLM\WIM_System %disk%Windows\System32\config\SYSTEM
reg load HKLM\WIM_Default %disk%Users\Default\NTUSER.DAT

Reg Add "HKLM\WIM_Software\Microsoft\PolicyManager\default\Browser\AllowSmartScreen" /v "value" /t REG_DWORD /d "1" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Explorer" /v "SmartScreenEnabled" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.Defender.SecurityCenter" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Run" /v "SecurityHealth" /t REG_EXPAND_SZ /d "%%windir%%\system32\SecurityHealthSystray.exe" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender" /v "DisableAntiSpyware" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender" /v "DisableAntiVirus" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender" /v "PUAProtection" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender\Features" /v "TamperProtection" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableAntiSpywareRealtimeProtection" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableIOAVProtection" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableOnAccessProtection" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableRealtimeMonitoring" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableScanOnRealtimeEnable" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DpaDisabled" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\MpCmdRun.exe" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\MsMpEng.exe" /v "Debugger" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\SecurityHealthService.exe" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\smartscreen.exe" /f

Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance\" /Enable" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender1" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Cleanup\" /Enable" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender2" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan\" /Enable" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender3" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Verification\" /Enable" /f

Reg Delete "HKLM\WIM_Software\Policies\Microsoft\Edge" /f
Reg Delete "HKLM\WIM_Software\Policies\Microsoft\Windows\System" /v "EnableSmartScreen" /f
Reg Delete "HKLM\WIM_Software\Policies\Microsoft\Windows Defender" /f
Reg Delete "HKLM\WIM_System\ControlSet001\Control\CI\Policy" /v "VerifiedAndReputablePolicyState" /f
Reg Add "HKLM\WIM_System\ControlSet001\Control\WMI\Autologger\DefenderApiLogger" /v "Start" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_System\ControlSet001\Control\WMI\Autologger\DefenderAuditLogger" /v "Start" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\SecurityHealthService" /v "Start" /t REG_DWORD /d "3" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\Sense" /v "Start" /t REG_DWORD /d "3" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdBoot" /v "Start" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdFilter" /v "Start" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdNisDrv" /v "Start" /t REG_DWORD /d "3" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdNisSvc" /v "Start" /t REG_DWORD /d "3" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WinDefend" /v "Start" /t REG_DWORD /d "2" /f

reg unload HKLM\WIM_Software
reg unload HKLM\WIM_System
reg unload HKLM\WIM_Default

DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.log*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.blf*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.regtrans-ms*"
DEL /F /S /Q /A:h "%disk%Windows\System32\SMI\Store\Machine\*.log*"
DEL /F /S /Q /A:h "%disk%Users\Default\*.log*"

pause
