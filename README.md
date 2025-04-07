# FilesCloud

`FilesCloud` — это веб-приложение для загрузки, хранения и скачивания файлов.

## Функции

- Регистрация и вход пользователей
- Загрузка и скачивание файлов
- Безопасное хранение файлов
- Удаление файлов

## Установка

1. **Клонируйте репозиторий:**

    ```bash
    git clone https://github.com/ваше_имя_пользователя/filescloud.git
    cd filescloud
    ```

2. **Создайте виртуальное окружение и установите зависимости:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # На Windows используйте `venv\Scripts\activate`
    pip install -r requirements.txt
    python.exe -m pip install --upgrade pip
    ```

3. **Настройте базу данных:**

    ```bash
    flask db init
    flask db migrate -m "Начальная миграция."
    flask db upgrade
    ```

4. **Запустите приложение:**

    ```bash
    python run.py
    ```

5. Откройте браузер и перейдите по адресу `http://127.0.0.1:5000/`

6. **Если порт занят другой задачей:**

    Убедитесь, что другое приложение не использует порт `5000`. Вы можете проверить это, выполнив команду в командной строке `Windows`

    ```bash
    netstat -aon | findstr :5000
    ```

```textline
filescloud/
│
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── forms.py
│   └── utils.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   └── register.html
│
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── scripts.js
│
├── uploads/
│   └── (файлы пользователей будут храниться здесь)
│
├── .gitignore
├── .env
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

```
Flask
Flask-SQLAlchemy
Flask-Login
Flask-Migrate
Flask-WTF
Werkzeug
```

## Использование

1. Зарегистрируйтесь или войдите в систему.
2. Загрузите файлы через форму на главной странице.
3. **Управляйте своими файлами:** скачивайте или удаляйте их.

## Вклад в проект

Если вы хотите внести свой вклад в проект, пожалуйста, создайте форк репозитория и отправьте `pull request`

Мы ценим любые улучшения и предложения.

## Лицензия

Этот проект лицензирован под лицензией `MIT`

Подробнее см. в файле `LICENSE`

## Контакты

Если у вас есть вопросы или предложения, пожалуйста, свяжитесь с нами по адресу `example@example.com`
