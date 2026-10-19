@echo off
rem Entry point for Windows terminals. Runs scripts\<command>.sh with Git Bash.
rem Usage: gitops setup ^| ci-watch ^| release ^| release broken ^| fix-broken ^| drift-demo ^| rollback ^| status ^| teardown
setlocal
set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%BASH%" (
  for /f "delims=" %%G in ('where git 2^>nul') do if not defined GITCMD set "GITCMD=%%~dpG"
)
if not exist "%BASH%" if defined GITCMD set "BASH=%GITCMD%..\bin\bash.exe"
if not exist "%BASH%" (
  echo Git Bash not found. Install Git for Windows.
  exit /b 1
)
if "%~1"=="" (
  echo Usage: gitops ^<command^> [args]
  echo.
  echo   setup          build the whole environment ^(cluster, registry, Gitea, ArgoCD, app^)
  echo   ci-watch       CI server: build and deploy every push to the source repo
  echo   release        developer pushes a new version of the app
  echo   release broken push a commit with failing tests ^(CI blocks it^)
  echo   fix-broken     revert the broken commit
  echo   drift-demo     change the cluster by hand and watch ArgoCD undo it
  echo   rollback       revert the last deployment through Git
  echo   open           open the app, ArgoCD and Gitea in the browser
  echo   status         show services, sync state, pods and history
  echo   teardown       delete everything
  exit /b 0
)
if not exist "%~dp0scripts\%~1.sh" (
  echo Unknown command: %~1
  exit /b 1
)
"%BASH%" "%~dp0scripts\%~1.sh" %2 %3 %4
exit /b %ERRORLEVEL%
