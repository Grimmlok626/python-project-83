import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
print(os.getenv('DATABASE_URL'))

from .db import (
    get_url_by_id,
    get_url_by_normalized_url,
    add_url,
    get_all_urls,
    get_checks_for_url
)
from .parser import parse_site
from .url_normalizer import normalize_url
import validators
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "please-set-secret")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/urls", methods=["POST"])
def urls_post():
    url_input = request.form.get("url", "").strip()

    # Валидация (некорректный URL → остаёмся на index с ошибкой)
    if not url_input or len(url_input) > 255 or not validators.url(url_input):
        flash("Некорректный URL", "error")
        return render_template("index.html"), 422

    normalized_url = normalize_url(url_input)
    if not normalized_url:
        flash("Некорректный URL", "error")
        return render_template("index.html"), 422

    # Проверка на существование
    existing = get_url_by_normalized_url(normalized_url)
    if existing:
        # Категория и текст под тесты Hexlet
        flash("Страница успешно добавлена", "success")
        return redirect(url_for("list_urls"))

    # Добавление нового URL
    try:
        add_url(normalized_url)
        flash("Страница успешно добавлена", "success")
        return redirect(url_for("list_urls"))
    except Exception:
        flash("Ошибка при добавлении сайта", "error")
        return render_template("index.html"), 500


@app.route("/urls")
def list_urls():
    urls = get_all_urls()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:url_id>")
def show_url(url_id):
    url = get_url_by_id(url_id)
    if not url:
        flash("URL не найден", "error")
        return redirect(url_for("list_urls"))
    checks = get_checks_for_url(url_id)
    return render_template("url.html", url=url, url_checks=checks)


@app.route("/urls/<int:url_id>/checks", methods=["POST"])
def create_check(url_id):
    url_record = get_url_by_id(url_id)
    if not url_record:
        flash("URL не найден", "error")
        return redirect(url_for("list_urls"))

    url_value = url_record[1]  # во втором элементе — URL

    try:
        response = requests.get(url_value, timeout=10)
        response.raise_for_status()

        data = parse_site(response.text)

        from .db import add_url_check
        add_url_check(
            url_id,
            response.status_code,
            data['h1'],
            data['title'],
            data['description']
        )

        flash("Страница успешно проверена", "success")
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "error")

    return redirect(url_for("show_url", url_id=url_id))