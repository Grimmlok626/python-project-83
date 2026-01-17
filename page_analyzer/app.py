import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'default-secret-key'  # или лучше требовать обязательно переменную окружения

@app.route('/')
def index():
    return 'Hello, Hexlet!'