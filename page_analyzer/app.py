import os
from flask import Flask, render_template, request, redirect, url_for, flash
from urllib.parse import urlparse
from datetime import datetime
import validators
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

from .db import (
    get_url_by_id,
    get_url_by_normalized_url,
    add_url,
    get_all_urls,
    get_checks_for_url,
    add_url_check
)
from .url_normalizer import normalize_url

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "please-set-secret")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/urls", methods=["POST"])
def urls_post():
    raw_url = request.form["url"].strip()
    # 1. Проверяем корректность
    if not validators.url(raw_url):
        flash("Некорректный URL", "danger")
        return redirect(url_for("index"))

    # 2. Нормализуем
    normalized = normalize_url(raw_url)

    # 3. Ищем в БД
    existing = get_url_by_normalized_url(normalized)
    if existing:
        url_id = existing[0]
        flash("Страница уже существует", "info")
        return redirect(url_for("show_url", url_id=url_id))

    # 4. Добавляем новую запись
    url_id = add_url(normalized)  # ваша функция должна вернуть только что созданный id
    flash("Страница успешно добавлена", "success")
    return redirect(url_for("show_url", url_id=url_id))


@app.route("/urls", methods=["GET"])
def list_urls():
    urls = get_all_urls()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:url_id>", methods=["GET"])
def show_url(url_id):
    url_record = get_url_by_id(url_id)
    if not url_record:
        flash("URL не найден", "danger")
        return redirect(url_for("list_urls"))

    checks = get_checks_for_url(url_id)
    return render_template("url.html", url=url_record, url_checks=checks)


@app.route("/urls/<int:url_id>/checks", methods=["POST"])
def create_check(url_id):
    # 1. Убедимся, что URL есть в БД
    url_record = get_url_by_id(url_id)
    if not url_record:
        flash("Страница не найдена", "danger")
        return redirect(url_for("index"))

    url = url_record[1]  # предполагаем, что вторым полем возвращается normalized URL

    try:
        # 2. Запрашиваем страницу
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()

        # 3. Парсим ответ
        soup = BeautifulSoup(resp.text, "html.parser")
        status_code = resp.status_code
        h1 = soup.h1.string.strip() if soup.h1 else ""
        title = soup.title.string.strip() if soup.title else ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        description = desc_tag["content"].strip() if desc_tag and desc_tag.has_attr("content") else ""

        # 4. Сохраняем в БД
        checked_at = datetime.now()
        add_url_check(
            url_id=url_id,
            status_code=status_code,
            h1=h1,
            title=title,
            description=description,
            created_at=checked_at,
        )
        flash("Страница успешно проверена", "success")

    except Exception:
        flash("Не удалось проверить страницу", "danger")

    return redirect(url_for("show_url", url_id=url_id))


if __name__ == "__main__":
    app.run(debug=True)