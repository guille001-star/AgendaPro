# Script para crear la estructura del proyecto AgendaPro

 $projectName = "agenda_pro"

# Crear directorios principales
New-Item -ItemType Directory -Force -Path $projectName
New-Item -ItemType Directory -Force -Path "$projectName\app"
New-Item -ItemType Directory -Force -Path "$projectName\app\static\css"
New-Item -ItemType Directory -Force -Path "$projectName\app\static\js"
New-Item -ItemType Directory -Force -Path "$projectName\app\static\img"
New-Item -ItemType Directory -Force -Path "$projectName\app\templates\auth"
New-Item -ItemType Directory -Force -Path "$projectName\app\templates\dashboard"
New-Item -ItemType Directory -Force -Path "$projectName\app\templates\public"
New-Item -ItemType Directory -Force -Path "$projectName\app\routes"
New-Item -ItemType Directory -Force -Path "$projectName\app\models"
New-Item -ItemType Directory -Force -Path "$projectName\app\utils"
New-Item -ItemType Directory -Force -Path "$projectName\migrations"
New-Item -ItemType Directory -Force -Path "$projectName\tests"

# Crear archivos de configuración y entorno
New-Item -ItemType File -Force -Path "$projectName\requirements.txt"
New-Item -ItemType File -Force -Path "$projectName\config.py"
New-Item -ItemType File -Force -Path "$projectName\.env"
New-Item -ItemType File -Force -Path "$projectName\.gitignore"
New-Item -ItemType File -Force -Path "$projectName\run.py"

# Crear archivos de la app (Init y Rutas)
New-Item -ItemType File -Force -Path "$projectName\app\__init__.py"
New-Item -ItemType File -Force -Path "$projectName\app\routes\auth.py"
New-Item -ItemType File -Force -Path "$projectName\app\routes\dashboard.py"
New-Item -ItemType File -Force -Path "$projectName\app\routes\public.py"
New-Item -ItemType File -Force -Path "$projectName\app\models\user.py"
New-Item -ItemType File -Force -Path "$projectName\app\models\appointment.py"
New-Item -ItemType File -Force -Path "$projectName\app\utils\qr_generator.py"

# Crear Templates HTML (Base y principales)
New-Item -ItemType File -Force -Path "$projectName\app\templates\base.html"
New-Item -ItemType File -Force -Path "$projectName\app\templates\auth\login.html"
New-Item -ItemType File -Force -Path "$projectName\app\templates\dashboard\index.html"
New-Item -ItemType File -Force -Path "$projectName\app\templates\public\agenda.html"

# Inicializar Git
Set-Location $projectName
git init
Set-Location ..

Write-Host "¡Estructura creada exitosamente en la carpeta '$projectName'!" -ForegroundColor Green