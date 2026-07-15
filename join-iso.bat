@echo off
rem join-iso.bat -- recombine split mochios ISO parts and verify checksum
rem usage: place in same dir as *.iso.part.* files and run

setlocal enabledelayedexpansion
set "out=mochios.iso"

if exist "%out%" (
    echo %out% already exists, deleting...
    del "%out%"
)

echo recombining parts into %out%...
copy /b "*.iso.part.aa" + "*.iso.part.ab" + "*.iso.part.ac" + "*.iso.part.ad" + "*.iso.part.ae" + "*.iso.part.af" "%out%" > nul

if not exist "%out%" (
    echo error: failed to create %out%
    exit /b 1
)

echo done.

rem verify checksum if available
if exist "SHA256SUMS.txt" (
    echo verifying checksum...
    for /f "tokens=1" %%a in ('findstr /i "%out%" SHA256SUMS.txt ^| find /v ""') do set "expected=%%a"
    if not "!expected!"=="" (
        for /f %%h in ('certutil -hashfile "%out%" SHA256 ^| find /v ":"') do set "actual=%%h"
        if "!actual!"=="!expected!" (
            echo checksum: OK
        ) else (
            echo checksum: MISMATCH -- iso is corrupted!
            echo expected: !expected!
            echo actual:   !actual!
            exit /b 1
        )
    ) else (
        echo no checksum found for %out% in SHA256SUMS.txt, skipping verification
    )
) else (
    echo no SHA256SUMS.txt found, skipping verification
)

dir /a "%out%"
