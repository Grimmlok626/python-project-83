import os
import psycopg2

def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise Exception("Переменная DATABASE_URL не установлена")


    return psycopg2.connect(url)

def get_url_by_id(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, url, created_at FROM urls WHERE id=%s;", (url_id,))
            return cur.fetchone()

def get_url_by_normalized_url(normalized_url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, url, created_at FROM urls WHERE url=%s;", (normalized_url,))
            return cur.fetchone()

def add_url(normalized_url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO urls (url) VALUES (%s) 
                ON CONFLICT (url) DO NOTHING 
                RETURNING id;
            """, (normalized_url,))
            result = cur.fetchone()
            if result:
                return result[0]
            else:
                cur.execute("SELECT id FROM urls WHERE url=%s;", (normalized_url,))
                return cur.fetchone()[0]

def get_all_urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.url, u.created_at,
                       uc.latest_check_at,
                       uc.latest_status_code
                FROM urls u
                LEFT JOIN (
                  SELECT DISTINCT ON (url_id) url_id, latest_check_at, latest_status_code
                  FROM url_checks
                  ORDER BY url_id, latest_check_at DESC
                ) uc ON u.id = uc.url_id
                ORDER BY u.id DESC;
            """)
            return cur.fetchall()

def get_checks_for_url(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, status_code, h1, title, description, created_at 
                FROM url_checks 
                WHERE url_id=%s 
                ORDER BY created_at DESC;
            """, (url_id,))
            return cur.fetchall()

def add_url_check(url_id, status_code, h1, title, description):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO url_checks (
                    url_id, status_code, h1, title, description, 
                    latest_check_at, latest_status_code
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW(), %s
                )
            """, (url_id, status_code, h1, title, description, status_code))
            conn.commit()