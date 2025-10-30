# FreeRADIUS - Fix Hung Sessions

Script automatizado para detectar y corregir sesiones colgadas (hung sessions) en bases de datos FreeRADIUS.

## 📋 Descripción

Este script identifica sesiones de usuarios que no han recibido actualizaciones de accounting en un periodo de tiempo definido y las cierra correctamente, estableciendo:

- `acctstoptime`: Última actualización conocida de la sesión
- `acctsessiontime`: Duración real de la sesión en segundos
- `acctterminatecause`: 'Session-Timeout'

## ✨ Características

- ✅ **Logging estructurado**: Sistema de logging completo con timestamps y niveles
- ✅ **Validación robusta**: Verificación de variables de entorno al inicio
- ✅ **Manejo de errores**: Try-catch en todas las operaciones críticas con rollback automático
- ✅ **Cálculo preciso**: `acctsessiontime` calculado correctamente desde `acctstarttime`
- ✅ **Modo Dry-Run**: Prueba sin modificar datos, ideal para verificar cambios antes de aplicarlos
- ✅ **Modo Debug**: Muestra todos los queries SQL ejecutados para troubleshooting y auditoría
- ✅ **Docker ready**: Contenedor listo para producción con ejecución periódica
- ✅ **Códigos de salida**: Códigos específicos para diferentes tipos de errores

## 🔧 Requisitos

- Python 3.12+
- MySQL/MariaDB con esquema FreeRADIUS
- Acceso de lectura/escritura a la tabla `radacct`

## 📦 Instalación

### Opción 1: Ejecución local con Python

```bash
# Clonar el repositorio
git clone <repository-url>
cd freeradius-fix-hung-sessions

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DB_HOST=192.168.1.100
export DB_USER=radius
export DB_PASSWORD=yourpassword
export DB_DATABASE=radius
export HUNG_SESSION_THRESHOLD=60
```

### Opción 2: Docker (recomendado para producción)

```bash
# Clonar el repositorio
git clone <repository-url>
cd freeradius-fix-hung-sessions

# Crear docker-compose.override.yaml con tus credenciales
# (ver sección de configuración más abajo)

# Construir y ejecutar
docker-compose up -d
```

## ⚙️ Configuración

### Variables de entorno requeridas

| Variable | Descripción | Ejemplo | Requerida |
|----------|-------------|---------|-----------|
| `DB_HOST` | Host de la base de datos | `192.168.1.100` | ✅ Sí |
| `DB_USER` | Usuario de la base de datos | `radius` | ✅ Sí |
| `DB_PASSWORD` | Contraseña del usuario | `secretpassword` | ✅ Sí |
| `DB_DATABASE` | Nombre de la base de datos | `radius` | ✅ Sí |
| `HUNG_SESSION_THRESHOLD` | Minutos sin actualización para considerar sesión colgada | `60` | ❌ No (default: 60) |
| `DRY_RUN` | Modo de prueba (solo registra sin modificar datos) | `true`, `false`, `1`, `0`, `yes`, `no` | ❌ No (default: false) |
| `DEBUG` | Modo debug (muestra queries SQL ejecutados) | `true`, `false`, `1`, `0`, `yes`, `no` | ❌ No (default: false) |
| `EXEC_INTERVAL` | Segundos entre ejecuciones (solo Docker) | `300` | ❌ No (default: 3600) |

### Customización con docker-compose.override.yaml

El archivo `docker-compose.yaml` incluye valores placeholder que deben ser sobrescritos para tu entorno. **No modifiques el archivo base**, en su lugar crea un archivo `docker-compose.override.yaml`:

```bash
# Crear archivo de configuración personalizada
cat > docker-compose.override.yaml << 'EOF'
services:
  radius_session_fixer:
    environment:
      DB_HOST: 192.168.1.100
      DB_USER: radiususer
      DB_PASSWORD: mySecurePassword123
      DB_DATABASE: radius
      HUNG_SESSION_THRESHOLD: 15  # 15 minutos
      EXEC_INTERVAL: 300          # cada 5 minutos
      DRY_RUN: false              # cambiar a 'true' para modo prueba
      DEBUG: false                # cambiar a 'true' para ver queries SQL
EOF
```

> **Nota**: El archivo `docker-compose.override.yaml` es ignorado por Git automáticamente y Docker Compose lo fusionará automáticamente con el archivo base al ejecutar `docker-compose up`.

## 🚀 Uso

### Ejecución manual

```bash
# Definir variables de entorno inline
DB_HOST=192.168.1.100 DB_USER=radius DB_PASSWORD=pass DB_DATABASE=radius python fix_sessions.py

# O exportarlas en la sesión actual
export DB_HOST=192.168.1.100
export DB_USER=radius
export DB_PASSWORD=pass
export DB_DATABASE=radius
python fix_sessions.py
```

### Modo Dry-Run (prueba sin modificar datos)

El modo dry-run permite ejecutar el script para ver qué sesiones serían modificadas sin realizar cambios reales en la base de datos:

```bash
# Ejecutar en modo dry-run
DRY_RUN=true DB_HOST=192.168.1.100 DB_USER=radius DB_PASSWORD=pass DB_DATABASE=radius python fix_sessions.py

# O con exportación de variables
export DB_HOST=192.168.1.100
export DB_USER=radius
export DB_PASSWORD=pass
export DB_DATABASE=radius
export DRY_RUN=true
python fix_sessions.py

# También acepta otros valores: 1, yes, y (case-insensitive)
DRY_RUN=1 python fix_sessions.py
DRY_RUN=yes python fix_sessions.py
```

### Modo Debug (ver queries SQL ejecutados)

El modo debug muestra todos los queries SQL que se ejecutan en la base de datos, útil para troubleshooting y auditoría:

```bash
# Ejecutar en modo debug
DEBUG=true DB_HOST=192.168.1.100 DB_USER=radius DB_PASSWORD=pass DB_DATABASE=radius python fix_sessions.py

# Combinar con dry-run para ver los queries sin ejecutarlos
DEBUG=true DRY_RUN=true DB_HOST=192.168.1.100 DB_USER=radius DB_PASSWORD=pass DB_DATABASE=radius python fix_sessions.py

# O con exportación de variables
export DB_HOST=192.168.1.100
export DB_USER=radius
export DB_PASSWORD=pass
export DB_DATABASE=radius
export DEBUG=true
python fix_sessions.py

# También acepta otros valores: 1, yes, y (case-insensitive)
DEBUG=1 python fix_sessions.py
DEBUG=yes python fix_sessions.py
```

### Ejecución con Docker

```bash
# Iniciar el contenedor
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Detener el contenedor
docker-compose down
```

### Ejecución con cron (Linux)

```bash
# Editar crontab
crontab -e

# Ejecutar cada 5 minutos
*/5 * * * * cd /path/to/freeradius-fix-hung-sessions && /usr/bin/python3 fix_sessions.py >> /var/log/radius_fixer.log 2>&1
```

## 📊 Ejemplo de salida

### Sesiones encontradas y corregidas

```
2025-10-30 10:15:23 - INFO - Variables de entorno validadas correctamente
2025-10-30 10:15:23 - INFO - Iniciando búsqueda de sesiones colgadas (threshold=60 minutos)
2025-10-30 10:15:23 - INFO - Conectado exitosamente a la base de datos en 192.168.1.100
2025-10-30 10:15:23 - INFO - Encontradas 3 sesiones colgadas
2025-10-30 10:15:23 - INFO - Iniciando corrección de 3 sesiones colgadas...
2025-10-30 10:15:23 - INFO - Sesión actualizada: radacctid=12345, username=user@domain.com, duration=3600s
2025-10-30 10:15:23 - INFO - Sesión actualizada: radacctid=12346, username=user2@domain.com, duration=7200s
2025-10-30 10:15:23 - INFO - Sesión actualizada: radacctid=12347, username=user3@domain.com, duration=1800s
2025-10-30 10:15:23 - INFO - Commit exitoso: 3 sesiones actualizadas
2025-10-30 10:15:23 - INFO - Proceso completado exitosamente
2025-10-30 10:15:23 - INFO - Conexión cerrada
```

### Modo Dry-Run (sin modificar datos)

```
2025-10-30 10:30:15 - INFO - Variables de entorno validadas correctamente
2025-10-30 10:30:15 - INFO - *** MODO DRY-RUN ACTIVADO - No se modificarán datos ***
2025-10-30 10:30:15 - INFO - Iniciando búsqueda de sesiones colgadas (threshold=60 minutos)
2025-10-30 10:30:15 - INFO - Conectado exitosamente a la base de datos en 192.168.1.100
2025-10-30 10:30:15 - INFO - Encontradas 3 sesiones colgadas
2025-10-30 10:30:15 - INFO - Iniciando corrección de 3 sesiones colgadas...
2025-10-30 10:30:15 - INFO - [DRY-RUN] Sesión que se actualizaría: radacctid=12345, username=user@domain.com, duration=3600s, acctstoptime=2025-10-30 09:30:15, acctterminatecause=Session-Timeout
2025-10-30 10:30:15 - INFO - [DRY-RUN] Sesión que se actualizaría: radacctid=12346, username=user2@domain.com, duration=7200s, acctstoptime=2025-10-30 08:30:15, acctterminatecause=Session-Timeout
2025-10-30 10:30:15 - INFO - [DRY-RUN] Sesión que se actualizaría: radacctid=12347, username=user3@domain.com, duration=1800s, acctstoptime=2025-10-30 10:00:15, acctterminatecause=Session-Timeout
2025-10-30 10:30:15 - INFO - [DRY-RUN] No se realizaron cambios en la base de datos (3 sesiones analizadas)
2025-10-30 10:30:15 - INFO - Proceso completado exitosamente
2025-10-30 10:30:15 - INFO - Conexión cerrada
```

### Modo Debug (mostrando queries SQL)

```
2025-10-30 10:45:30 - INFO - Variables de entorno validadas correctamente
2025-10-30 10:45:30 - INFO - *** MODO DEBUG ACTIVADO - Se mostrarán todos los queries SQL ***
2025-10-30 10:45:30 - INFO - Iniciando búsqueda de sesiones colgadas (threshold=60 minutos)
2025-10-30 10:45:30 - INFO - Conectado exitosamente a la base de datos en 192.168.1.100
2025-10-30 10:45:30 - DEBUG - [SQL] Query: SELECT radacctid, username, acctstarttime, acctupdatetime FROM radacct WHERE acctstoptime IS NULL AND acctupdatetime < (NOW() - INTERVAL %s MINUTE) | Params: (60,)
2025-10-30 10:45:30 - INFO - Encontradas 2 sesiones colgadas
2025-10-30 10:45:30 - INFO - Iniciando corrección de 2 sesiones colgadas...
2025-10-30 10:45:30 - DEBUG - [SQL] Query: UPDATE radacct SET acctstoptime = %s, acctterminatecause = %s, acctsessiontime = %s WHERE radacctid = %s | Params: (datetime.datetime(2025, 10, 30, 9, 45, 30), 'Session-Timeout', 3600, 12345)
2025-10-30 10:45:30 - INFO - Sesión actualizada: radacctid=12345, username=user@domain.com, duration=3600s
2025-10-30 10:45:30 - DEBUG - [SQL] Query: UPDATE radacct SET acctstoptime = %s, acctterminatecause = %s, acctsessiontime = %s WHERE radacctid = %s | Params: (datetime.datetime(2025, 10, 30, 8, 45, 30), 'Session-Timeout', 7200, 12346)
2025-10-30 10:45:30 - INFO - Sesión actualizada: radacctid=12346, username=user2@domain.com, duration=7200s
2025-10-30 10:45:30 - INFO - Commit exitoso: 2 sesiones actualizadas
2025-10-30 10:45:30 - INFO - Proceso completado exitosamente
2025-10-30 10:45:30 - INFO - Conexión cerrada
```

### Sin sesiones colgadas

```
2025-10-30 10:20:45 - INFO - Variables de entorno validadas correctamente
2025-10-30 10:20:45 - INFO - Iniciando búsqueda de sesiones colgadas (threshold=60 minutos)
2025-10-30 10:20:45 - INFO - Conectado exitosamente a la base de datos en 192.168.1.100
2025-10-30 10:20:45 - INFO - Encontradas 0 sesiones colgadas
2025-10-30 10:20:45 - INFO - No se encontraron sesiones colgadas
2025-10-30 10:20:45 - INFO - Conexión cerrada
```

### Ejemplo de error (variables faltantes)

```
2025-10-30 10:25:12 - ERROR - Faltan variables de entorno requeridas: DB_HOST, DB_PASSWORD
2025-10-30 10:25:12 - ERROR - Error de configuración: Variables de entorno faltantes: DB_HOST, DB_PASSWORD
```

## 🔍 Funcionamiento técnico

El script realiza las siguientes operaciones:

1. **Validación**: Verifica que todas las variables de entorno requeridas estén configuradas
2. **Conexión**: Establece conexión segura con la base de datos MySQL/MariaDB
3. **Búsqueda**: Ejecuta query SQL para encontrar sesiones sin `acctstoptime` y con `acctupdatetime` antiguo:
   ```sql
   SELECT radacctid, username, acctstarttime, acctupdatetime
   FROM radacct
   WHERE acctstoptime IS NULL
     AND acctupdatetime < (NOW() - INTERVAL {threshold} MINUTE)
   ```
4. **Corrección**: Para cada sesión encontrada:
   - Establece `acctstoptime = acctupdatetime`
   - Calcula `acctsessiontime = (acctstoptime - acctstarttime)` en segundos
   - Establece `acctterminatecause = 'Session-Timeout'`
5. **Commit**: Confirma todos los cambios en una sola transacción
6. **Rollback automático**: Si ocurre algún error, deshace todos los cambios

## 🛠️ Troubleshooting

### Error: "Unable to import 'pymysql'"

```bash
# Instalar dependencias
pip install -r requirements.txt
```

### Error: "Access denied for user"

- Verificar credenciales en variables de entorno
- Verificar permisos del usuario en la base de datos:
  ```sql
  GRANT SELECT, UPDATE ON radius.radacct TO 'radiususer'@'%';
  FLUSH PRIVILEGES;
  ```

### Error: "Can't connect to MySQL server"

- Verificar que el host sea accesible: `ping DB_HOST`
- Verificar que MySQL esté escuchando en el puerto correcto: `telnet DB_HOST 3306`
- Verificar firewall y reglas de seguridad

### El contenedor se reinicia constantemente

```bash
# Ver logs del contenedor
docker-compose logs -f

# Verificar que las variables de entorno estén correctas
docker-compose config
```

## 📋 Códigos de salida

| Código | Descripción |
|--------|-------------|
| 0 | Ejecución exitosa |
| 1 | Error de configuración (variables de entorno faltantes) |
| 2 | Error de base de datos (conexión o query) |
| 99 | Error inesperado |

## 📝 Estructura del proyecto

```
freeradius-fix-hung-sessions/
├── fix_sessions.py                  # Script principal
├── requirements.txt                 # Dependencias Python
├── Dockerfile                       # Imagen Docker
├── docker-compose.yaml              # Configuración Docker Compose base
├── docker-compose.override.yaml*    # Configuración personalizada (no versionado)
├── README.md                        # Esta documentación
└── .gitignore                       # Archivos ignorados por Git

* Archivo opcional para customización local
```

## 🔒 Seguridad

- ✅ No almacena credenciales en el código
- ✅ Variables de entorno para configuración sensible
- ✅ `docker-compose.override.yaml` incluido en `.gitignore`
- ✅ Conexiones con timeout configurado
- ✅ Uso de prepared statements (prevención SQL injection)
- ⚠️ Recomendado: Usar `cryptography` para conexiones SSL/TLS

### Habilitar SSL/TLS (recomendado)

Modificar `connect_db()` en `fix_sessions.py`:

```python
connection = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_DATABASE'),
    cursorclass=pymysql.cursors.DictCursor,
    ssl={'ssl': True}  # Agregar esta línea
)
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👤 Autor

**Tu Nombre/Organización**

## 🙏 Agradecimientos

- Proyecto FreeRADIUS
- Comunidad de Python y PyMySQL

---

**¿Necesitas ayuda?** Abre un issue en el repositorio.

