import os
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import psycopg2
import validators

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
                        # Уже существует, возвратим его id
                        cur.execute("SELECT id FROM urls WHERE name=%s;", (url_input,))
                        url_id = cur.fetchone()[0]
            flash("Страница успешно добавлена", "success")
            return redirect(url_for("show_url", url_id=url_id))
        except Exception as e:
            flash("Ошибка при добавлении URL", "error")
            return render_template("index.html")

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
            # Получите проверки
            cur.execute("SELECT * FROM url_checks WHERE url_id=%s ORDER BY created_at DESC;", (url_id,))
            url_checks = cur.fetchall()
    if not url_record:
        flash("URL не найден", "error")
        return redirect(url_for("list_urls"))
    return render_template("url.html", url=url_record, url_checks=url_checks)

from flask import jsonify

@app.route('/urls/<int:url_id>/checks', methods=['POST'])
def create_check(url_id):
    # В этой версии просто создаем запись с текущей датой и id
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO url_checks (url_id, created_at)
                VALUES (%s, NOW())
                RETURNING id, created_at;
                ''',
                (url_id,)
            )
            check = cur.fetchone()
    # Возвращаем id и дату проверки
    return jsonify({'id': check[0], 'created_at': check[1].isoformat()})