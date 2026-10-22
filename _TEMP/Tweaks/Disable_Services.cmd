

::
:: Disable Services  =============================================================================================================================
::

set disk=C:\

reg load HKLM\WIM_System %disk%Windows\System32\config\SYSTEM


:: Telemetry service
Reg Add "HKLM\WIM_System\ControlSet001\Services\DiagTrack" /v "Start" /t REG_DWORD /d "0x4" /f

:: Indexing Service
Reg Add "HKLM\WIM_System\ControlSet001\Services\WSearch" /v "Start" /t REG_DWORD /d "0x4" /f

::  Client tracking of changed relationships
Reg Add "HKLM\WIM_System\ControlSet001\Services\TrkWks" /v "Start" /t REG_DWORD /d "4" /f

::  Print Manager
rem Reg Add "HKLM\WIM_System\ControlSet001\Services\Spooler" /v "Start" /t REG_DWORD /d "4" /f
rem Reg Add "HKLM\WIM_System\ControlSet001\Services\Spooler" /v "Start" /t REG_DWORD /d "4" /f

::  Windows Error Logging Service
Reg Add "HKLM\WIM_System\ControlSet001\Services\WerSvc" /v "Start" /t REG_DWORD /d "4" /f

:: Downloaded map manager
Reg Add "HKLM\WIM_System\ControlSet001\Services\MapsBroker" /v "Start" /t REG_DWORD /d "4" /f

:: Geographic Location Service
Reg Add "HKLM\WIM_System\ControlSet001\Services\lfsvc" /v "Start" /t REG_DWORD /d "4" /f



reg unload HKLM\WIM_System


DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.log*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.blf*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.regtrans-ms*"
DEL /F /S /Q /A:h "%disk%Windows\System32\SMI\Store\Machine\*.log*"
DEL /F /S /Q /A:h "%disk%Users\Default\*.log*"

pause
