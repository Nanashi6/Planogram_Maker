### Planogram-Maker
---
Перед началом работы нужно:
- установить все пакеты из requirements.txt
- создать файл .flaskenv в корне проекта со следующим содержимым
    ```text
    FLASK_APP = app.py
    SECRET_KEY = <CSRF_TOKEN_KEY>
    SQLALCHEMY_DATABASE_URI = <DATABASE_URL> 

    ITEMS_PER_PAGE = 25

    FLASK_DEBUG=1
    ```