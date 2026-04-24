import pymysql
import socket
from pymysql import Error

# --- CONFIGURACIÓN CON EL NUEVO HOSTNAME ---
HOST_TEST = 'cpl16.main-hosting.eu'
USER_TEST = 'saltaped_finanza'
PASS_TEST = r'fina7625' 
DB_TEST   = 'saltaped_finanza'

def diagnostico_db():
    print(f"--- DIAGNÓSTICO EN {HOST_TEST} ---")
    
    # 1. Probar resolución de nombre y puerto
    try:
        ip_resuelta = socket.gethostbyname(HOST_TEST)
        print(f"1. Hostname resuelto a la IP: {ip_resuelta}")
        socket.create_connection((HOST_TEST, 3306), timeout=5)
        print("   ✅ Puerto 3306 abierto.")
    except Exception as e:
        print(f"   ❌ ERROR DE RED: {e}")
        return

    # 2. Intento de conexión
    print(f"2. Conectando como '{USER_TEST}'...")
    conn = None
    try:
        conn = pymysql.connect(
            host=HOST_TEST,
            user=USER_TEST,
            password=PASS_TEST,
            database=DB_TEST,
            port=3306,
            # Forzamos el uso de una conexión limpia
            init_command='SET NAMES utf8mb4',
            connect_timeout=10
        )
        
        if conn.open:
            print("   ✅ ¡CONEXIÓN EXITOSA!")
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()
                print(f"   📊 Versión MySQL: {version[0] if isinstance(version, tuple) else version['VERSION()']}")

    except Error as e:
        error_code = e.args[0]
        print(f"   ❌ ERROR DE MYSQL ({error_code}): {e}")
        if error_code == 1045:
            print("\n   ⚠️  PUNTOS A REVISAR:")
            print(f"   - En el panel de Hostinger, ¿el usuario '{USER_TEST}' tiene privilegios en '{DB_TEST}'?")
            print(f"   - ¿La contraseña en el script coincide EXACTAMENTE con la del panel?")
            print(f"   - En 'MySQL Remoto', ¿el usuario '{USER_TEST}' está habilitado para '%'?")
            
    finally:
        if conn and conn.open:
            conn.close()
            print("\n--- PROCESO FINALIZADO ---")

if __name__ == "__main__":
    diagnostico_db()