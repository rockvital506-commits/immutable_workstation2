

::
:: Prevent Device Encryption  ===================================================================================================================================
::

set disk=C:\


reg load HKLM\WIM_System %disk%Windows\System32\config\SYSTEM

Reg Add "HKLM\WIM_System\ControlSet001\Control\BitLocker" /v "PreventDeviceEncryption" /t REG_DWORD /d "1" /f


reg unload HKLM\WIM_System


DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.log*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.blf*"
DEL /F /S /Q /A:h "%disk%Windows\System32\config\*.regtrans-ms*"
DEL /F /S /Q /A:h "%disk%Windows\System32\SMI\Store\Machine\*.log*"
DEL /F /S /Q /A:h "%disk%Users\Default\*.log*"

pause
