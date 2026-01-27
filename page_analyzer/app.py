import os
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
import validators
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from .db import (
    get_url_by_id,
    get_url_by_normalized_url,
    add_url,
    get_all_urls,
    get_checks_for_url,
    add_url_check,
)
from .url_normalizer import normalize_url

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "please-set-secret")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/urls", methods=["POST"])
def urls_post():
    raw_url = request.form.get("url", "").strip()
    if not validators.url(raw_url):
        flash("Некорректный URL", "danger")
        return render_template("index.html"), 422

    normalized = normalize_url(raw_url)
    existing = get_url_by_normalized_url(normalized)
    if existing:
        flash("Страница уже существует", "info")
        return redirect(url_for("show_url", url_id=existing[0]))

    url_id = add_url(normalized)
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
    url_record = get_url_by_id(url_id)
    if not url_record:
        flash("Страница не найдена", "danger")
        return redirect(url_for("list_urls"))

    url = url_record[1]
    try:
        # получаем страницу
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()

        # парсим
        soup = BeautifulSoup(resp.text, "html.parser")
        status_code = resp.status_code
        h1 = soup.h1.string.strip() if soup.h1 and soup.h1.string else ""
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        desc_tag = soup.find(
            "meta",
            attrs={"name": "description"},
        )
        description = (
            desc_tag["content"].strip()
            if desc_tag and desc_tag.has_attr("content")
            else ""
        )

        # сохраняем в БД
        add_url_check(
            url_id=url_id,
            status_code=status_code,
            h1=h1,
            title=title,
            description=description,
            created_at=datetime.now(),
        )

        # важный flash
        flash("Страница успешно проверена", "success")

    except requests.RequestException:
        # не удалось достучаться до сайта или статус != 200
        flash("Произошла ошибка при проверке", "danger")

    return redirect(url_for("show_url", url_id=url_id))


if __name__ == "__main__":
    app.run(debug=True)
