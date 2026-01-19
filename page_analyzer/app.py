import os
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import psycopg2
import validators
import requests
from bs4 import BeautifulSoup  # импортируем для парсинга HTML

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "please-set-secret")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url_input = request.form.get("url", "").strip()
        # Валидация
        if not url_input:
            flash("Введите URL", "error")
            return render_template("index.html")
        if len(url_input) > 255:
            flash("URL не должен превышать 255 символов", "error")
            return render_template("index.html")
        if not validators.url(url_input):
            flash("Некорректный URL", "error")
            return render_template("index.html")
        # Проверка и вставка в базу
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id;", (url_input,))
                    result = cur.fetchone()
                    if result:
                        url_id = result[0]
                    else:
                        cur.execute("SELECT id FROM urls WHERE name=%s;", (url_input,))
                        url_id = cur.fetchone()[0]
            flash("Страница успешно добавлена", "success")
            return redirect(url_for("show_url", url_id=url_id))
        except Exception:
            flash("Ошибка при добавлении URL", "error")
    return render_template("index.html")

@app.route("/urls")
def list_urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls ORDER BY id DESC;")
            urls = cur.fetchall()
    return render_template("urls.html", urls=urls)

@app.route("/urls/<int:url_id>")
def show_url(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id=%s;", (url_id,))
            url_record = cur.fetchone()
            cur.execute("SELECT * FROM url_checks WHERE url_id=%s ORDER BY created_at DESC;", (url_id,))
            url_checks = cur.fetchall()
    if not url_record:
        flash("URL не найден", "error")
        return redirect(url_for("list_urls"))
    return render_template("url.html", url=url_record, url_checks=url_checks)

@app.route('/urls/<int:url_id>/checks', methods=['POST'])
def create_check(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Получаем URL из базы
            cur.execute("SELECT name FROM urls WHERE id=%s;", (url_id,))
            record = cur.fetchone()
            if not record:
                flash("URL не найден", "error")
                return redirect(url_for("show_url", url_id=url_id))
            full_url = record[0]
            try:
                response = requests.get(full_url, timeout=10)
                response.raise_for_status()
                status_code = response.status_code

                # Парсим HTML через BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Получение <h1>
                h1_tag = soup.find('h1')
                h1_text = h1_tag.get_text(strip=True) if h1_tag else ''

                # Получение <title>
                title_tag = soup.find('title')
                title_text = title_tag.get_text(strip=True) if title_tag else ''

                # Получение <meta name="description" content="...">
                meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
                description_content = meta_desc_tag['content'].strip() if meta_desc_tag and 'content' in meta_desc_tag.attrs else ''

                # Вставляем данные в таблицу
                cur.execute(
                    '''
                    INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ''',
                    (url_id, status_code, h1_text, title_text, description_content)
                )
                flash("Проверка выполнена успешно", "success")
            except requests.RequestException:
                flash("Произошла ошибка при проверке", "error")
    return redirect(url_for("show_url", url_id=url_id))