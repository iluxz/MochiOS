@echo off
rem join-iso.bat -- recombine split mochios ISO parts
rem usage: place in same dir as *.iso.part.* files and run

setlocal enabledelayedexpansion
set "out=mochios.iso"

if exist "%out%" (
    echo %out% already exists, deleting...
    del "%out%"
)

echo recombining parts into %out%...
copy /b "*.iso.part.aa" + "*.iso.part.ab" + "*.iso.part.ac" + "*.iso.part.ad" + "*.iso.part.ae" + "*.iso.part.af" "%out%" > nul

if exist "%out%" (
    echo done: %out% (%out% bytes)
    certutil -hashfile "%out%" SHA256
) else (
    echo error: failed to create %out%
    exit /b 1
)
