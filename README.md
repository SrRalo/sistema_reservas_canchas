🏟️ Sistema de Reservas de Canchas
Sistema web desarrollado con Streamlit y PostgreSQL/Supabase para la gestión integral de reservas de canchas deportivas.
📋 Características Principales

✅ 3 Roles de Usuario: Administrador, Operador, Consultor
✅ Gestión Completa: Canchas, Clientes, Reservas, Pagos
✅ Reportes Avanzados: Con joins múltiples y estadísticas
✅ Auditoría Completa: Bitácora automática de todas las acciones
✅ Interfaz Intuitiva: Dashboard responsive con Streamlit
✅ Base de Datos Robusta: PostgreSQL con triggers y funciones


🚀 Instalación y Configuración
Prerrequisitos
Antes de comenzar, asegúrate de tener instalado:

Python 3.8+ (Descargar Python)
Git (Descargar Git)
Cuenta en Supabase (Crear cuenta gratuita)

1. 📥 Clonar el Repositorio
bash# Clonar el proyecto
git clone https://github.com/tu-usuario/sistema-reservas-canchas.git

# Navegar al directorio
cd sistema-reservas-canchas
2. 🐍 Crear Entorno Virtual
En Windows:
bash# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate
En macOS/Linux:
bash# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

Nota: Verás (venv) al inicio de tu terminal cuando el entorno esté activado.

3. 📦 Instalar Dependencias
bash# Actualizar pip
pip install --upgrade pip

# Instalar dependencias del proyecto
pip install -r requirements.txt
4. 🗄️ Configurar Base de Datos en Supabase
4.1 Crear Proyecto en Supabase

Ve a Supabase y crea una cuenta
Crea un nuevo proyecto
Espera a que se complete la configuración (2-3 minutos)

4.2 Obtener Credenciales

En tu proyecto Supabase, ve a Settings → Database
Copia la Connection String (formato PostgreSQL)
En Settings → API, copia:

Project URL
Project API Key (anon/public)



4.3 Ejecutar Script de Base de Datos

En Supabase, ve a SQL Editor
Crea una nueva query
Copia y pega todo el contenido del archivo de tu script SQL
Ejecuta el script (puede tomar 1-2 minutos)

5. ⚙️ Configurar Variables de Entorno
5.1 Crear archivo .env
bash# Crear archivo de configuración
cp .env.example .env
5.2 Editar .env con tus credenciales
bash# Abrir con tu editor favorito
nano .env
# o
code .env
5.3 Completar configuración:
env# Configuración de Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-clave-publica-aqui

# Configuración de Base de Datos PostgreSQL
DATABASE_URL=postgresql://postgres:[password]@db.[proyecto].supabase.co:5432/postgres

# Configuración de la aplicación
APP_TITLE=Sistema Reservas Canchas
APP_ICON=🏟️
SECRET_KEY=tu-clave-secreta-muy-larga-y-segura-aqui

# Configuración de auditoría
AUDIT_ENABLED=true
SESSION_TIMEOUT=3600
6. 🎯 Ejecutar la Aplicación
bash# Asegúrate de que el entorno virtual esté activado
# Deberías ver (venv) en tu terminal

# Ejecutar la aplicación
streamlit run main.py
La aplicación se abrirá automáticamente en tu navegador en: http://localhost:8501

👥 Usuarios de Prueba
El sistema viene con usuarios predefinidos para pruebas:
RolEmailContraseñaPermisosAdministradoradmin@reservas.comadmin123Acceso completo + AuditoríaOperadoroperador@reservas.comoperador123Gestión operativa (sin auditoría)Consultorconsultor@reservas.comconsultor123Solo reportes (lectura)

📁 Estructura del Proyecto
sistema_reservas_canchas/
├── 📄 main.py                     # Aplicación principal
├── 📁 pages/                      # Páginas de la aplicación
│   ├── 01_🏟️_Gestión_Canchas.py
│   ├── 02_👥_Gestión_Clientes.py
│   ├── 03_📊_Reportes.py
│   └── 06_🔍_Auditoría.py
├── 📁 components/                 # Componentes reutilizables
│   ├── auth.py                    # Autenticación
│   ├── database.py                # Conexión BD
│   └── utils.py                   # Utilidades
├── 📄 requirements.txt            # Dependencias
├── 📄 .env                        # Variables de entorno
└── 📄 README.md                   # Este archivo

🛠️ Desarrollo
Comandos Útiles
bash# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Desactivar entorno virtual
deactivate

# Instalar nueva dependencia
pip install nombre-paquete
pip freeze > requirements.txt

# Ejecutar en modo desarrollo
streamlit run main.py --server.runOnSave true
Variables de Entorno de Desarrollo
env# Configuración adicional para desarrollo
DEBUG=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
LOG_LEVEL=DEBUG

🔧 Solución de Problemas
Error: "ModuleNotFoundError"
bash# Verificar que el entorno virtual esté activado
which python  # Debe mostrar la ruta del venv

# Reinstalar dependencias
pip install -r requirements.txt
Error de conexión a Base de Datos

Verifica que las credenciales en .env sean correctas
Confirma que el proyecto Supabase esté activo
Revisa que el script SQL se haya ejecutado completamente

Error: "streamlit: command not found"
bash# Instalar Streamlit globalmente
pip install streamlit

# O usar con python -m
python -m streamlit run main.py
Puerto ocupado
bash# Usar otro puerto
streamlit run main.py --server.port 8502

📊 Funcionalidades por Rol
👑 Administrador

Gestión completa de canchas y tipos
CRUD de clientes y reservas
Configuración de horarios y precios
Acceso a todos los reportes
Acceso exclusivo a auditoría

👨‍💼 Operador

Gestión operativa de canchas
CRUD de clientes
Creación y seguimiento de reservas
Registro de pagos
Reportes operativos

👁️ Consultor

Solo acceso a reportes
Consulta de estadísticas
Visualización de datos históricos
Sin permisos de modificación


🚀 Despliegue en Producción
Opciones Recomendadas:

Streamlit Cloud (Gratuito)

Conecta tu repositorio GitHub
Configuración automática
SSL incluido


Heroku (Gratuito con limitaciones)

Requiere Procfile
Configuración de variables de entorno


DigitalOcean App Platform

Escalable
Configuración con app.yaml




📞 Soporte
Si encuentras algún problema:

📖 Revisa esta documentación
🐛 Verifica la sección de solución de problemas
📧 Contacta al equipo de desarrollo


📄 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

¡Sistema listo para usar! 🎉
Recuerda mantener activado tu entorno virtual cada vez que trabajes en el proyecto.
