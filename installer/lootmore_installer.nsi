; Lootmore NSIS installer template
!include "MUI2.nsh"

!define APPNAME "Lootmore"
!define APPEXE "Lootmore.exe"
!define APPGUID "{7C3C1D45-5B2F-4F4E-9E20-LOOTMORE}"
!define VERSION "@VERSION@"

Name "${APPNAME} ${VERSION}"
OutFile "${OUTPUT}"
InstallDir "$PROGRAMFILES\\${APPNAME}"
RequestExecutionLevel user

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "${APPEXE}"
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  WriteRegStr HKCU "Software\\${APPNAME}" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\\${APPEXE}"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
  DeleteRegKey HKCU "Software\\${APPNAME}"
SectionEnd
