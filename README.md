# Мелок — журнал тренировок (хостинг-версия)

Та же самая веб-страница, но теперь данные хранятся не в браузере, а на сервере
в SQLite. Значит, если открыть приложение и с телефона, и с компьютера —
тренировки будут одинаковые с обеих сторон.

Доступ закрыт одним общим паролем (без регистрации — это же личное
приложение на одного человека).

## Структура проекта

```
melok-app/
  main.py            — backend на FastAPI
  requirements.txt
  Procfile            — команда запуска для Railway/Render
  static/index.html   — фронтенд (то же приложение, но ходит в API)
```

## Деплой на Railway (бесплатно, проще всего)

1. **Залей код на GitHub.**
   В папке `melok-app`:
   ```
   git init
   git add .
   git commit -m "melok fitness app"
   ```
   Создай пустой репозиторий на github.com и запушь туда:
   ```
   git remote add origin https://github.com/<твой-юзернейм>/melok-app.git
   git push -u origin main
   ```

2. **Зайди на [railway.app](https://railway.app)**, залогинься через GitHub.

3. **New Project → Deploy from GitHub repo** → выбери `melok-app`.
   Railway сам увидит `requirements.txt` и `Procfile` и соберёт проект
   (Nixpacks, Python).

4. **Добавь переменную окружения** (вкладка Variables):
   - `APP_PASSWORD` = какой-нибудь свой пароль, например `train2026!`

5. **Важно: подключи Volume, чтобы данные не терялись при передеплое.**
   Во вкладке проекта → **Volumes → New Volume**, примонтируй, например,
   к пути `/data`. Затем добавь ещё одну переменную окружения:
   - `DB_PATH` = `/data/melok.db`

   Если пропустить этот шаг — приложение всё равно будет работать,
   но при каждом обновлении кода база пересоздастся с нуля.

6. **Settings → Generate Domain** — Railway выдаст публичную ссылку вида
   `https://melok-app-production.up.railway.app`. Это и есть твой адрес.

7. Открой эту ссылку на телефоне и на компьютере, введи пароль — готово,
   данные общие.

## Альтернатива: Render.com

Тоже бесплатно, только Free-инстанс "засыпает" после 15 минут без запросов
(первое открытие после паузы займёт секунд 20–30 на "пробуждение"):

1. New → Web Service → подключи тот же GitHub-репозиторий.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. В Environment добавь `APP_PASSWORD`.
5. Для постоянного хранения данных подключи Render Disk (аналог Volume),
   примонтируй к `/data`, добавь `DB_PATH=/data/melok.db`.

## Как пользоваться с телефона

Открой ссылку в мобильном браузере → войди по паролю → на Android/iOS
через меню браузера выбери **"Добавить на главный экран"** — иконка
будет открываться как обычное приложение, без адресной строки.

## Локальный запуск (проверить перед деплоем)

```
pip install -r requirements.txt
APP_PASSWORD=test123 uvicorn main:app --reload
```
Открой `http://localhost:8000`.
