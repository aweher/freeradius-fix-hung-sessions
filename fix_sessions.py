import pymysql
import os
from datetime import timedelta

def connect_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_DATABASE'),
        cursorclass=pymysql.cursors.DictCursor
    )

def find_hung_sessions(connection, threshold_minutes):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT radacctid, username, acctupdatetime
            FROM radacct
            WHERE acctstoptime IS NULL
              AND acctupdatetime < (NOW() - INTERVAL %s MINUTE)
        """, (threshold_minutes,))
        return cursor.fetchall()

def fix_hung_sessions(connection, sessions, interval_minutes):
    with connection.cursor() as cursor:
        for session in sessions:
            stop_time = session['acctupdatetime'] + timedelta(minutes=interval_minutes)
            cursor.execute("""
                UPDATE radacct 
                SET acctstoptime = %s, acctterminatecause = %s 
                WHERE radacctid = %s
            """, (stop_time, 'Session-Timeout', session['radacctid']))
            print(f"Fixed session {session['radacctid']} for user {session['username']}.")
    connection.commit()

def main():
    threshold = int(os.getenv('HUNG_SESSION_THRESHOLD', '60'))
    interval = int(os.getenv('STOP_INTERVAL', '5'))

    conn = connect_db()
    try:
        sessions = find_hung_sessions(conn, threshold)
        if sessions:
            print(f"Found {len(sessions)} hung sessions. Fixing...")
            fix_hung_sessions(conn, sessions, interval)
        else:
            print("No hung sessions found.")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
