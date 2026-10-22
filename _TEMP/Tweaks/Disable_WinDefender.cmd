

::
:: Disable WinDefender  =============================================================================================================================
::

set disk=C:\

reg load HKLM\WIM_Software %disk%Windows\System32\config\Software
reg load HKLM\WIM_System %disk%Windows\System32\config\SYSTEM
reg load HKLM\WIM_Default %disk%Users\Default\NTUSER.DAT

Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Explorer" /v "SmartScreenEnabled" /t REG_SZ /d "Off" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows\System" /v "EnableSmartScreen" /t REG_DWORD /d "0" /f
Reg Delete "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Run" /v "SecurityHealth" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender" /v "DisableAntiVirus" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender" /v "PUAProtection" /t REG_DWORD /d "0" /f

Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender\Features" /v "TamperProtection" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableAntiSpywareRealtimeProtection" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableRealtimeMonitoring" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DpaDisabled" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableOnAccessProtection" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableScanOnRealtimeEnable" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows Defender\Real-Time Protection" /v "DisableIOAVProtection" /t REG_DWORD /d "1" /f

Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableRealtimeMonitoring" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableBehaviorMonitoring" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableIOAVProtection" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableOnAccessProtection" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableScanOnRealtimeEnable" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows\System" /v "EnableSmartScreen" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender" /v "DisableAntiVirus" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\SmartScreen" /v "ConfigureAppInstallControl" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\SmartScreen" /v "ConfigureAppInstallControlEnabled" /t REG_DWORD /d "1" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Edge" /v "SmartScreenEnabled" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Edge" /v "SmartScreenPuaEnabled" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\Spynet" /v "SpyNetReporting" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Software\Policies\Microsoft\Windows Defender\Spynet" /v "SubmitSamplesConsent" /t REG_DWORD /d "2" /f
Reg Add "HKLM\WIM_Software\Microsoft\PolicyManager\default\Browser\AllowSmartScreen" /f /v value /t REG_DWORD /d "0"

Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.Defender.SecurityCenter" /v "Enabled" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance" /v "Enabled" /t REG_DWORD /d "0" /f

Reg Add "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\MpCmdRun.exe" /v "Debugger" /t REG_SZ /d "NUL" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\MsMpEng.exe" /v "Debugger" /t REG_SZ /d "NUL" /f
rem Reg Add "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\SecurityHealthService.exe" /v "Debugger" /t REG_SZ /d "NUL" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\smartscreen.exe" /v "Debugger" /t REG_SZ /d "NUL" /f

Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance\" /Disable" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender1" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Cleanup\" /Disable" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender2" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan\" /Disable" /f
Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "Defender3" /t REG_SZ /d "schtasks /Change /TN \"\Microsoft\Windows\Windows Defender\Windows Defender Verification\" /Disable" /f

Reg Add "HKLM\WIM_System\ControlSet001\Control\CI\Policy" /v "VerifiedAndReputablePolicyState" /t REG_DWORD /d "0" /f
rem Reg Add "HKLM\WIM_System\ControlSet001\Services\SecurityHealthService" /v "Start" /t REG_DWORD /d "3" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WinDefend" /v "Start" /t REG_DWORD /d "4" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\Sense" /v "Start" /t REG_DWORD /d "4" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdBoot" /v "Start" /t REG_DWORD /d "4" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdFilter" /v "Start" /t REG_DWORD /d "4" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdNisDrv" /v "Start" /t REG_DWORD /d "4" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\WdNisSvc" /v "Start" /t REG_DWORD /d "4" /f
rem Reg Add "HKLM\WIM_System\ControlSet001\Services\wscsvc" /v "Start" /t REG_DWORD /d "4" /f

Reg Add "HKLM\WIM_Default\WIM_Software\Microsoft\Windows\CurrentVersion\AppHost" /v "EnableWebContentEvaluation" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Default\WIM_Software\Microsoft\Windows\CurrentVersion\AppHost" /v "PreventOverride" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Default\WIM_Software\Microsoft\Windows Security Health\State" /v "AppAndBrowser_StoreAppsSmartScreenOff" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_Default\WIM_Software\Microsoft\Edge\SmartScreenEnabled" /ve /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_System\ControlSet001\Control\WMI\Autologger\DefenderApiLogger" /v "Start" /t REG_DWORD /d "0" /f
Reg Add "HKLM\WIM_System\ControlSet001\Control\WMI\Autologger\DefenderAuditLogger" /v "Start" /t REG_DWORD /d "0" /f

reg unload HKLM\WIM_Software
reg unload HKLM\WIM_System
reg unload HKLM\WIM_Default


DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.log*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.blf*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.regtrans-ms*"
DEL /F /S /Q /A:h "%disk%Windows\System32\SMI\Store\Machine\*.log*"
DEL /F /S /Q /A:h "%disk%Users\Default\*.log*"

pause
