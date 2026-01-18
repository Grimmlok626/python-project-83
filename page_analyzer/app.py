import os
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder=os.path.join(basedir, '..', 'templates'))
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "please-set-secret")

@app.get("/")
def index():
    return render_template("index.html")