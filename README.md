# Yatube
### Описание
Социальная сеть с возможность публиковать посты, посещать страницы авторов, подписываться, а так же комментировать записи.
### Запуск проекта в dev-режиме
Клонируем репозиторий на свой компьютер
```
git clone https://github.com/Pash1et/homework_bot.git
```
Переходим в папку с файлами и устанавливаем виртуальное окружение
```
python -m venv venv
```
Активируем виртуальное окружение
```
source venv/script/Activate
```
Установите зависимости из файла requirements.txt
```
python -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Выполнить миграции:

```
python api_yamdb/manage.py migrate
```

Запустить проект:

```
python yatube/manage.py runserver
```
