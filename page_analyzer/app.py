import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from dotenv import load_dotenv
import psycopg2
import validators

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url_input = request.form.get('url', '').strip()
        error = None

        if len(url_input) > 255:
            error = 'URL не должен превышать 255 символов'
        elif not validators.url(url_input):
            error = 'Некорректный URL'

        if error:
            flash(error, 'danger')
            return render_template('index.html', url=url_input)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM urls WHERE name = %s;", (url_input,))
                    if cur.fetchone():
                        flash('Данный сайт уже добавлен', 'warning')
                    else:
                        cur.execute("INSERT INTO urls (name) VALUES (%s);", (url_input,))
                        conn.commit()
                        # Получаем id добавленной записи
                        cur.execute("SELECT id FROM urls WHERE name = %s;", (url_input,))
                        url_id = cur.fetchone()[0]
                        return redirect(url_for('show_url', url_id=url_id))
        except Exception as e:
            flash('Ошибка базы данных', 'danger')
            print(e)
    return render_template('index.html')

@app.route('/urls')
def urls():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC;")
            urls_list = cur.fetchall()
    return render_template('urls.html', urls=urls_list)

@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s;", (url_id,))
            url_entry = cur.fetchone()
            if url_entry is None:
                abort(404)
    return render_template('url.html', url=url_entry)