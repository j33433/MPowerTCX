;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "MPowerTCX"
  OutFile "Install MPowerTCX.exe"

  ;Default installation folder
  InstallDir "$LOCALAPPDATA\MPowerTCX"

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\MPowerTCX" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING
  !define MUI_ICON "..\..\images\mpowertcx-icon.ico"

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "MPowerTCX" SecDummy
  SetOutPath "$INSTDIR"
  File /r "..\build\exe.win-amd64-2.7"
	
  WriteRegStr HKCU "Software\MPowerTCX" "" $INSTDIR

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  CreateDirectory "$SMPROGRAMS\MPowerTCX"
  CreateShortCut "$SMPROGRAMS\MPowerTCX\MPowerTCX.lnk" "$INSTDIR\exe.win-amd64-2.7\mpowertcx.exe" ""
  CreateShortCut "$SMPROGRAMS\MPowerTCX\Uninstall MPowerTCX.lnk" "$INSTDIR\Uninstall.exe" ""
  CreateShortCut "$DESKTOP\MPowerTCX.lnk" "$INSTDIR\exe.win-amd64-2.7\mpowertcx.exe" ""
SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecDummy ${LANG_ENGLISH} "MPowerTCX"

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$SMPROGRAMS\MPowerTCX\MPowerTCX.lnk"
  Delete "$SMPROGRAMS\MPowerTCX\Uninstall MPowerTCX.lnk"
  RMDir "$SMPROGRAMS\MPowerTCX"
  Delete "$DESKTOP\MPowerTCX.lnk"
  
  RMDir /r "$INSTDIR\exe.win-amd64-2.7"
  RMDir "$INSTDIR"

  DeleteRegKey /ifempty HKCU "Software\Modern UI Test"
SectionEnd
