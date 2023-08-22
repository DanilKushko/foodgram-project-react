# Онлайн-сервис «Продуктовый помощник»
## Описание
На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.


## Технологии
- Python 3.10
- Django
- Django REST Framework


## Учетные данные администратора
- Логин: docker_admin
- Пароль: docker_admin


## Проект доступен по ссылкам:
```
https://foodgram.freedynamicdns.net/

https://foodgram.freedynamicdns.net/admin/
```


## Запуск проекта
- Клонировала репозиторий foodgram-project-react
- Перейти в директорию infra
```
cd foodgram-project-react/infra
```
- В папке infra выполнить команду 
```
docker-compose up
```


## После запуска увидеть спецификацию API вы сможете по адресу:
```
 http://localhost/api/docs/
```


## Backend
```
cd foodgram-project-react
```
- Cоздать и активировать виртуальное окружение:
```
python -m venv env
```
```
source venv/Scripts/activate
```
```
python -m pip install --upgrade pip
```
- Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
- Выполнить миграции:
```
python3 manage.py migrate
```
- Запустить проект:
```
python3 manage.py runserver
```


## Запустите миграции
```
python manage.py makemigrations
python manage.py migrate
```
## Создание суперюзера


```
python manage.py createsuperuser
```


## Запуск локально 
- Собираем контейнерыы:
- Из папки infra/ разверните контейнеры при помощи docker-compose:
```
docker-compose up -d --build
```
- Выполните миграции:
```
docker-compose exec backend python manage.py migrate
```
- Создайте суперпользователя:
```
winpty docker-compose exec backend python manage.py createsuperuser
```
- Соберите статику:
```
docker-compose exec backend python manage.py collectstatic --no-input
```
- Наполните базу данных ингредиентами и тегами. Выполняйте команду из дериктории где находится файл manage.py:
```
docker-compose exec backend python manage.py load_ingredients
```
- Остановка проекта:
```
docker-compose down
```


## Запустить проект на боевом сервере:
- Установить на сервере docker и docker-compose. Скопировать на сервер файлы docker-compose.yaml и default.conf:
- Cоздать и заполнить .env файл в директории infra
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres_fg
POSTGRES_USER=postgres_fg
POSTGRES_PASSWORD=postgres_fg
DB_HOST=db_fg
DB_PORT=5432
SECRET_KEY=
ALLOWED_HOSTS=
DEBUG=
```
cd infra
sudo docker compose -f docker-compose.yml pull
```
sudo docker compose -f docker-compose.yml down
```
sudo docker compose -f docker-compose.yml up -d
```
sudo docker compose -f docker-compose.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.yml exec backend cp -r /app/static/. /static/ 
```
Затем необходимо будет создать суперюзера и загрузить в базу данных информацию об ингредиентах:
```
sudo docker-compose exec web python manage.py createsuperuser
```
```
sudo docker-compose exec web python manage.py load_ingredients
```


## Автор
- Кушко Данил
```
https://github.com/DanilKushko
```