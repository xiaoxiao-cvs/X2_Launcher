!macro customInstall
  # 检查Python
  nsExec::ExecToStack 'python --version'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_YESNO "需要安装Python环境，是否现在安装?" IDYES installPython
    Goto done
    installPython:
    ExecWait '$INSTDIR\resources\python-3.9.0.exe /quiet InstallAllUsers=1 PrependPath=1'
  ${EndIf}
  
  # 安装依赖
  ExecWait 'pip install -r $INSTDIR\resources\requirements.txt'
  
  done:
!macroend
