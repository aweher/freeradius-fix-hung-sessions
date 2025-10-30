import pymysql
import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_env_vars():
    """Valida que todas las variables de entorno necesarias existan."""
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_DATABASE']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error("Faltan variables de entorno requeridas: %s", ', '.join(missing))
        raise EnvironmentError(f"Variables de entorno faltantes: {', '.join(missing)}")
    
    logger.info("Variables de entorno validadas correctamente")
    return True

def connect_db():
    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE'),
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info("Conectado exitosamente a la base de datos en %s", os.getenv('DB_HOST'))
        return connection
    except pymysql.Error as e:
        logger.error("Error al conectar a la base de datos: %s", e)
        raise

def find_hung_sessions(connection, threshold_minutes):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT radacctid, username, acctstarttime, acctupdatetime
                FROM radacct
                WHERE acctstoptime IS NULL
                  AND acctupdatetime < (NOW() - INTERVAL %s MINUTE)
            """, (threshold_minutes,))
            sessions = cursor.fetchall()
            logger.info("Encontradas %d sesiones colgadas", len(sessions))
            return sessions
    except pymysql.Error as e:
        logger.error("Error al buscar sesiones colgadas: %s", e)
        raise

def fix_hung_sessions(connection, sessions, dry_run=False):
    try:
        with connection.cursor() as cursor:
            for session in sessions:
                # Usar acctupdatetime como acctstoptime
                stop_time = session['acctupdatetime']
                
                # Calcular acctsessiontime (duración de la sesión en segundos)
                if session['acctstarttime']:
                    session_time = int((stop_time - session['acctstarttime']).total_seconds())
                else:
                    session_time = 0
                    logger.warning("Sesión %s no tiene acctstarttime", session['radacctid'])
                
                if dry_run:
                    logger.info(
                        "[DRY-RUN] Sesión que se actualizaría: radacctid=%s, username=%s, duration=%ds, "
                        "acctstoptime=%s, acctterminatecause=Session-Timeout",
                        session['radacctid'], session['username'], session_time, stop_time
                    )
                else:
                    cursor.execute("""
                        UPDATE radacct 
                        SET acctstoptime = %s, 
                            acctterminatecause = %s,
                            acctsessiontime = %s
                        WHERE radacctid = %s
                    """, (stop_time, 'Session-Timeout', session_time, session['radacctid']))
                    
                    logger.info(
                        "Sesión actualizada: radacctid=%s, username=%s, duration=%ds",
                        session['radacctid'], session['username'], session_time
                    )
        
        if dry_run:
            logger.info("[DRY-RUN] No se realizaron cambios en la base de datos (%d sesiones analizadas)", len(sessions))
        else:
            connection.commit()
            logger.info("Commit exitoso: %d sesiones actualizadas", len(sessions))
        
    except pymysql.Error as e:
        logger.error("Error al actualizar sesiones: %s", e)
        if not dry_run:
            connection.rollback()
            logger.info("Rollback ejecutado")
        raise

def main():
    try:
        # Validar variables de entorno
        validate_env_vars()
        
        # Obtener parámetros
        threshold = int(os.getenv('HUNG_SESSION_THRESHOLD', '60'))
        dry_run = os.getenv('DRY_RUN', 'false').lower() in ('true', '1', 'yes', 'y')
        
        if dry_run:
            logger.info("*** MODO DRY-RUN ACTIVADO - No se modificarán datos ***")
        
        logger.info("Iniciando búsqueda de sesiones colgadas (threshold=%d minutos)", threshold)
        
        # Conectar a la base de datos
        conn = connect_db()
        try:
            sessions = find_hung_sessions(conn, threshold)
            if sessions:
                logger.info("Iniciando corrección de %d sesiones colgadas...", len(sessions))
                fix_hung_sessions(conn, sessions, dry_run=dry_run)
                logger.info("Proceso completado exitosamente")
            else:
                logger.info("No se encontraron sesiones colgadas")
        finally:
            conn.close()
            logger.info("Conexión cerrada")
            
    except EnvironmentError as e:
        logger.error("Error de configuración: %s", e)
        sys.exit(1)
    except pymysql.Error as e:
        logger.error("Error de base de datos: %s", e)
        sys.exit(2)
    except Exception as e:
        logger.error("Error inesperado: %s", e, exc_info=True)
        sys.exit(99)

if __name__ == '__main__':
    main()
