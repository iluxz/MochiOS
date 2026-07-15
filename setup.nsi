!include "MUI2.nsh"
!include "LogicLib.nsh"

Name "Mochi"
OutFile "mochi-setup.exe"
InstallDir "$PROGRAMFILES64\Mochi"
RequestExecutionLevel admin

!define PRODUCT_NAME "Mochi"
!define PRODUCT_VERSION "0.1.0"
!define PRODUCT_PUBLISHER "MochiOS"
!define PRODUCT_WEB_SITE "https://mochios.dev"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"

  File "mochi\mochi.exe"

  File "mochi\beat.cmd"
  File "mochi\install.cmd"
  File "mochi\remove.cmd"
  File "mochi\uninstall.cmd"
  File "mochi\update.cmd"
  File "mochi\upgrade.cmd"
  File "mochi\search.cmd"
  File "mochi\status.cmd"
  File "mochi\deploy.cmd"
  File "mochi\rollback.cmd"
  File "mochi\snapshot.cmd"
  File "mochi\run.cmd"

  WriteUninstaller "$INSTDIR\uninstall.exe"

  DetailPrint "Adding Mochi to system PATH..."
  ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"
  ${If} $0 != ""
    StrCpy $0 "$0;$INSTDIR"
  ${Else}
    StrCpy $0 "$INSTDIR"
  ${EndIf}
  WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" $0
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\Mochi"
  CreateShortCut "$SMPROGRAMS\Mochi\Mochi Shell.lnk" "cmd.exe" "/k mochi help" "$INSTDIR\mochi.exe" 0
  CreateShortCut "$SMPROGRAMS\Mochi\Uninstall Mochi.lnk" "$INSTDIR\uninstall.exe"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\mochi.exe"
  Delete "$INSTDIR\beat.cmd"
  Delete "$INSTDIR\install.cmd"
  Delete "$INSTDIR\remove.cmd"
  Delete "$INSTDIR\uninstall.cmd"
  Delete "$INSTDIR\update.cmd"
  Delete "$INSTDIR\upgrade.cmd"
  Delete "$INSTDIR\search.cmd"
  Delete "$INSTDIR\status.cmd"
  Delete "$INSTDIR\deploy.cmd"
  Delete "$INSTDIR\rollback.cmd"
  Delete "$INSTDIR\snapshot.cmd"
  Delete "$INSTDIR\run.cmd"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"

  DetailPrint "Removing Mochi from system PATH..."
  ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"
  StrCpy $1 "$INSTDIR"
  StrLen $2 $1
  StrCpy $3 $0
  StrCpy $4 ""
  loop:
    StrCpy $5 $3 1
    ${If} $5 == ""
      ${If} $4 == $1
        StrCpy $3 ""
      ${EndIf}
      Goto done
    ${EndIf}
    ${If} $5 == ";"
      IntOp $2 $2 + 0
      ${If} $4 == $1
        StrCpy $3 "$3"
      ${Else}
        StrCpy $3 "$3;$4"
      ${EndIf}
      StrCpy $4 ""
    ${Else}
      StrCpy $4 "$4$5"
    ${EndIf}
    StrCpy $3 $3 "" 1
    Goto loop
  done:
  WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" $3
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

  SetShellVarContext all
  RMDir "$SMPROGRAMS\Mochi"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
