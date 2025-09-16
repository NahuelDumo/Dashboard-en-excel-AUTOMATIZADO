@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ========================================
echo   CREADOR DE PAQUETE DE DISTRIBUCIÓN
echo ========================================
echo.

:: Configuración
set PACKAGE_NAME=StreamlitApp_Portable

:: Eliminar carpeta existente (si existe)
if exist "%PACKAGE_NAME%" (
    echo [INFO] Eliminando paquete existente...
    rmdir /s /q "%PACKAGE_NAME%"
)

:: Crear carpeta de distribución
echo [INFO] Creando estructura de carpetas...
mkdir "%PACKAGE_NAME%"

:: Copiar archivos principales
echo [INFO] Copiando archivos de la aplicación...

if exist "app.py" (
    copy "app.py" "%PACKAGE_NAME%\" >nul
    echo   ✓ app.py copiado
) else (
    echo   ⚠ app.py no encontrado
)

if exist "assets" (
    xcopy "assets" "%PACKAGE_NAME%\assets\" /E /I /H /Y >nul 2>&1
    echo   ✓ Carpeta assets copiada
) else (
    echo   ⚠ Carpeta assets no encontrada
)

if exist "utils" (
    xcopy "utils" "%PACKAGE_NAME%\utils\" /E /I /H /Y >nul 2>&1
    echo   ✓ Carpeta utils copiada
) else (
    echo   ⚠ Carpeta utils no encontrada
)

:: Crear archivo de versión
echo 1.0.0 > "%PACKAGE_NAME%\version.txt"

echo [INFO] Creando archivos del instalador...

:: ========================
:: CREAR install.bat
:: ========================
(
echo @echo off
echo chcp 65001 ^>nul
echo setlocal EnableDelayedExpansion
echo.
echo echo.
echo echo ========================================
echo echo   INSTALADOR STREAMLIT APP PORTABLE
echo echo ========================================
echo echo.
echo echo [INFO] Este proceso instalará Python portable y todas las dependencias
echo echo Asegúrate de tener conexión a internet
echo echo.
echo echo Presiona cualquier tecla para continuar...
echo pause ^>nul
echo echo.
echo.
echo set PYTHON_VERSION=3.11.9
echo set PYTHON_URL=https://www.python.org/ftp/python/%%PYTHON_VERSION%%/python-%%PYTHON_VERSION%%-embed-amd64.zip
echo set PYTHON_DIR=%%~dp0python
echo set PYTHON_EXE=%%PYTHON_DIR%%\python.exe
echo set GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py
echo.
echo echo [INFO] Verificando instalación de Python...
echo if exist "%%PYTHON_EXE%%" ^(
echo     echo [INFO] Python portable ya está instalado
echo     goto :install_deps
echo ^)
echo.
echo echo [INFO] Creando directorio para Python...
echo if not exist "%%PYTHON_DIR%%" mkdir "%%PYTHON_DIR%%"
echo.
echo echo [INFO] Descargando Python %%PYTHON_VERSION%%...
echo powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%%PYTHON_URL%%' -OutFile 'python.zip' -UseBasicParsing; Write-Host 'Descarga completada' } catch { Write-Host 'Error en descarga: '$_.Exception.Message; exit 1 }"
echo if %%ERRORLEVEL%% neq 0 ^(
echo     echo [ERROR] Falló la descarga de Python
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo [INFO] Extrayendo Python...
echo powershell -Command "try { Expand-Archive -Path 'python.zip' -DestinationPath '%%PYTHON_DIR%%' -Force; Remove-Item 'python.zip' -Force; Write-Host 'Extracción completada' } catch { Write-Host 'Error extrayendo: '$_.Exception.Message; exit 1 }"
echo.
echo echo [INFO] Configurando Python portable...
echo echo import site ^>^> "%%PYTHON_DIR%%\python311._pth"
echo echo site-packages ^>^> "%%PYTHON_DIR%%\python311._pth"
echo.
echo echo [INFO] Descargando e instalando pip...
echo powershell -Command "try { Invoke-WebRequest -Uri '%%GET_PIP_URL%%' -OutFile 'get-pip.py' -UseBasicParsing; Write-Host 'pip descargado' } catch { Write-Host 'Error descargando pip: '$_.Exception.Message; exit 1 }"
echo "%%PYTHON_EXE%%" get-pip.py --quiet --no-warn-script-location
echo del get-pip.py
echo.
echo :install_deps
echo echo [INFO] Instalando dependencias de Streamlit...
echo echo   → streamlit
echo "%%PYTHON_EXE%%" -m pip install streamlit^>=1.28.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → pandas
echo "%%PYTHON_EXE%%" -m pip install pandas^>=1.5.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → plotly
echo "%%PYTHON_EXE%%" -m pip install plotly^>=5.15.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → openpyxl
echo "%%PYTHON_EXE%%" -m pip install openpyxl^>=3.0.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → xlsxwriter
echo "%%PYTHON_EXE%%" -m pip install xlsxwriter^>=3.0.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → xlrd
echo "%%PYTHON_EXE%%" -m pip install xlrd^>=2.0.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → numpy
echo "%%PYTHON_EXE%%" -m pip install numpy^>=1.24.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → pyarrow
echo "%%PYTHON_EXE%%" -m pip install pyarrow^>=10.0.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → requests
echo "%%PYTHON_EXE%%" -m pip install requests^>=2.28.0 --quiet --disable-pip-version-check --no-warn-script-location
echo echo   → kaleido ^(para exportar gráficos^)
echo "%%PYTHON_EXE%%" -m pip install kaleido --quiet --disable-pip-version-check --no-warn-script-location
echo.
echo echo [OK] ¡Instalación completada exitosamente!
echo echo.
echo echo Para ejecutar la aplicación, usa: run_app.bat
echo echo La aplicación se abrirá en: http://localhost:8501
echo echo.
echo pause
) > "%PACKAGE_NAME%\install.bat"

:: ========================
:: CREAR run_app.bat
:: ========================
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo echo ========================================
echo echo       STREAMLIT APP LAUNCHER
echo echo ========================================
echo echo.
echo.
echo if not exist "python\python.exe" ^(
echo     echo [ERROR] Python no está instalado.
echo     echo.
echo     echo Por favor ejecuta install.bat primero para instalar
echo     echo Python y todas las dependencias necesarias.
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo if not exist "app.py" ^(
echo     echo [ERROR] No se encontró el archivo app.py
echo     echo.
echo     echo Asegúrate de estar en el directorio correcto
echo     echo y que el archivo app.py esté presente.
echo     echo.
echo     pause  
echo     exit /b 1
echo ^)
echo.
echo echo [INFO] Iniciando aplicación Streamlit...
echo echo [INFO] La aplicación se abrirá en: http://localhost:8501
echo echo [INFO] Presiona Ctrl+C en esta ventana para detener la aplicación
echo echo.
echo echo ¡Espera unos segundos mientras se carga la aplicación!
echo echo.
echo echo.
echo "python\python.exe" -m streamlit run app.py --server.port=8501 --server.headless=true
echo.
echo echo.
echo echo Aplicación finalizada.
echo pause
) > "%PACKAGE_NAME%\run_app.bat"

:: ========================
:: CREAR toggle_auto_update.bat
:: ========================
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo echo ========================================
echo echo    CONFIGURACIÓN AUTO UPDATE
echo echo ========================================
echo echo.
echo echo.
echo set AUTO_UPDATE_FILE=%%~dp0auto_update.txt
echo set STATUS=false
echo.
echo if exist "%%AUTO_UPDATE_FILE%%" ^(
echo     set /p STATUS=^<"%%AUTO_UPDATE_FILE%%"
echo ^)
echo.
echo if /i "!STATUS!"=="true" ^(
echo     echo [INFO] Estado actual: HABILITADO
echo     echo.
echo     set /p CONFIRM="¿Deseas DESHABILITAR auto update? ^(S/N^): "
echo     if /i "!CONFIRM!"=="S" ^(
echo         echo false ^> "%%AUTO_UPDATE_FILE%%"
echo         echo.
echo         echo [OK] Auto update DESHABILITADO
echo     ^)
echo ^) else ^(
echo     echo [INFO] Estado actual: DESHABILITADO  
echo     echo.
echo     set /p CONFIRM="¿Deseas HABILITAR auto update? ^(S/N^): "
echo     if /i "!CONFIRM!"=="S" ^(
echo         echo true ^> "%%AUTO_UPDATE_FILE%%"
echo         echo.
echo         echo [OK] Auto update HABILITADO
echo     ^)
echo ^)
echo.
echo pause
) > "%PACKAGE_NAME%\toggle_auto_update.bat"

:: ========================
:: CREAR README.txt
:: ========================
(
echo ========================================
echo     STREAMLIT APP PORTABLE - README
echo ========================================
echo.
echo INSTALACIÓN RÁPIDA:
echo 1. Ejecuta: install.bat
echo    - Descargará Python portable
echo    - Instalará todas las dependencias automáticamente
echo.
echo 2. Ejecuta: run_app.bat  
echo    - Iniciará la aplicación Streamlit
echo    - Se abrirá automáticamente en http://localhost:8501
echo.
echo ARCHIVOS INCLUIDOS:
echo - install.bat ...................... Instalador principal
echo - run_app.bat ...................... Ejecutar aplicación
echo - toggle_auto_update.bat ........... Configurar auto-actualización
echo - app.py ........................... Aplicación principal de Streamlit
echo - version.txt ...................... Versión del paquete
echo - README.txt ....................... Este archivo
echo.
echo REQUISITOS DEL SISTEMA:
echo - Windows 10 o superior
echo - Conexión a internet ^(solo para la instalación inicial^)
echo - Aproximadamente 150MB de espacio libre
echo.
echo SOLUCIÓN DE PROBLEMAS:
echo - Si hay errores de instalación, ejecuta install.bat como administrador
echo - Si la aplicación no inicia, verifica que install.bat se ejecutó correctamente
echo - Para detener la aplicación, presiona Ctrl+C en la ventana de comandos
echo.
echo DESINSTALACIÓN:
echo Para desinstalar, simplemente elimina toda la carpeta.
echo No se instalan archivos en otras ubicaciones del sistema.
echo.
echo ========================================
echo Para soporte técnico, revisa los mensajes de error
echo que aparecen durante la instalación o ejecución.
echo ========================================
) > "%PACKAGE_NAME%\README.txt"

echo   ✓ install.bat creado
echo   ✓ run_app.bat creado  
echo   ✓ toggle_auto_update.bat creado
echo   ✓ README.txt creado

:: ========================
:: Comprimir el paquete
:: ========================
echo.
echo [INFO] Comprimiendo el paquete...

:: Usar PowerShell para comprimir
powershell -Command "try { if (Test-Path '%PACKAGE_NAME%.zip') { Remove-Item '%PACKAGE_NAME%.zip' -Force }; Compress-Archive -Path '%PACKAGE_NAME%\*' -DestinationPath '%PACKAGE_NAME%.zip' -CompressionLevel Optimal; Write-Host 'Compresión exitosa' -ForegroundColor Green } catch { Write-Host 'Error comprimiendo: '$_.Exception.Message -ForegroundColor Red; exit 1 }"

if %ERRORLEVEL% equ 0 (
    echo [OK] Paquete comprimido como "%PACKAGE_NAME%.zip"
) else (
    echo [ERROR] Error al comprimir el paquete
    goto :end
)

echo.
echo ========================================
echo           PROCESO COMPLETADO
echo ========================================
echo.
echo ¡El paquete "%PACKAGE_NAME%.zip" está listo para distribución!
echo.
echo Contenido del paquete:
dir /b "%PACKAGE_NAME%"
echo.
echo INSTRUCCIONES PARA EL USUARIO FINAL:
echo 1. Extraer el archivo ZIP
echo 2. Ejecutar install.bat (instala Python + dependencias)  
echo 3. Ejecutar run_app.bat (lanza la aplicación Streamlit)
echo.
echo La aplicación se abrirá en: http://localhost:8501

:end
echo.
echo Presiona cualquier tecla para salir...
pause >nul