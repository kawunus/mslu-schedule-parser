# Установка и запуск проекта

## 0. Клонировать репозиторий
Необходимо клонировать репозиторий на свою машину/сервер:
```
git clone https://github.com/kawunus/mslu-schedule-parser.git
cd mslu-schedule-parser
```

## 1. Получить кредиты от Google

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий.
3. Перейдите в APIs & Services → Credentials.
4. Нажмите Create Credentials → OAuth client ID.
5. Выберите Desktop App (для локального получения токена).
6. Скачайте файл `credentials.json` и положите его в корень проекта.

## 2. Настройка `.env`

1. Сделайте копию примера конфигурации:
```
cp .env.example .env
```
2. Откройте `.env` через любой текстовый редактор (`nano .env` или `micro .env`) и вставьте свои кредиты и настройки календарей:
```
TARGET_CALENDAR_ID=<ID личного календаря>
UPDATE_INTERVAL=86400
PAUSE_BETWEEN_REQUESTS=0.2
COLOR_LK=9
COLOR_SEM=10
COLOR_PZ=11
```

## 3. Получить токен от Google

!ВАЖНО!
Если вы хотите деплоить скрипт на сервер, этот шаг необходимо сделать локально на своей машине. У меня не получилось получить токен через консоль :(

1. Убедитесь, что у вас установлен Poetry и зависимости проекта:

```
poetry install
```
2. Запустите скрипт `get_token.py` через Poetry, чтобы получить токен:
```
poetry run python get_token.py
```
После успешного выполнения токен сохранится в token.json.


## 4. Запуск проекта
Это можно сделать двумя путями:

### Poetry
```
poetry run python main.py
```

### Docker
```
docker-compose build
docker-compose up -d
docker-compose logs -f
```
