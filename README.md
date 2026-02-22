# 📝 Счётчик заметок

Простое веб-приложение для управления заметками на **Flask** + **PostgreSQL** в Docker.

## 🚀 Функционал

- `/add/<text>` — добавить заметку
- `/count` — количество заметок
- `/list` — список всех заметок

## 🐳 Быстрый старт

```bash
# Клонировать
git clone https://github.com/inekruz/notes.git
cd notes

# Настроить
cp .env.example .env
# Отредактируйте .env под свои данные

# Запустить
docker-compose up -d --build

# Открыть в браузере
http://localhost:5000
