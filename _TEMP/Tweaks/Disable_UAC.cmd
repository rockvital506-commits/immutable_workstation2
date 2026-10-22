

::
:: Disable UAC  ===================================================================================================================================
::

set disk=C:\

reg load HKLM\WIM_Software %disk%Windows\System32\config\Software
reg load HKLM\WIM_System %disk%Windows\System32\config\SYSTEM

Reg Add "HKLM\WIM_Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "EnableLUA" /t REG_DWORD /d "0x0" /f
Reg Add "HKLM\WIM_System\ControlSet001\Services\luafv" /v "Start" /t REG_DWORD /d "4" /f

reg unload HKLM\WIM_Software
reg unload HKLM\WIM_System

DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.log*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.blf*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.regtrans-ms*"
DEL /F /S /Q /A:h "%disk%Windows\System32\SMI\Store\Machine\*.log*"
DEL /F /S /Q /A:h "%disk%Users\Default\*.log*"

pause
