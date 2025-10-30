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
cp env.example .env
# Editar .env con tus credenciales
```

### Opción 2: Docker (recomendado para producción)

```bash
# Clonar el repositorio
git clone <repository-url>
cd freeradius-fix-hung-sessions

# Editar docker-compose.yaml con tus credenciales
vim docker-compose.yaml

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
| `EXEC_INTERVAL` | Segundos entre ejecuciones (solo Docker) | `300` | ❌ No (default: 3600) |

### Ejemplo de configuración (docker-compose.yaml)

```yaml
services:
  radius_session_fixer:
    build: .
    container_name: radius_session_fixer
    restart: always
    environment:
      DB_HOST: 192.168.1.100
      DB_USER: radiususer
      DB_PASSWORD: mySecurePassword123
      DB_DATABASE: radius
      HUNG_SESSION_THRESHOLD: 15  # 15 minutos
      EXEC_INTERVAL: 300          # cada 5 minutos
```

## 🚀 Uso

### Ejecución manual

```bash
# Con variables de entorno en .env
export $(cat .env | xargs)
python fix_sessions.py

# O definirlas inline
DB_HOST=192.168.1.100 DB_USER=radius DB_PASSWORD=pass DB_DATABASE=radius python fix_sessions.py
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
├── fix_sessions.py       # Script principal
├── requirements.txt      # Dependencias Python
├── Dockerfile           # Imagen Docker
├── docker-compose.yaml  # Configuración Docker Compose
├── env.example          # Ejemplo de variables de entorno
├── README.md           # Esta documentación
└── .gitignore          # Archivos ignorados por Git
```

## 🔒 Seguridad

- ✅ No almacena credenciales en el código
- ✅ Variables de entorno para configuración sensible
- ✅ `.env` incluido en `.gitignore`
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

