## Инструкция по запуску проекта

1. Находясь в папке проекта, введи в терминале IDE следующие команды:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# deactivate
```

2. Для настройки СУБД postgresql-17 введи следующие команды:

```sh
sudo apt-get install libpq-dev
pip install psycopg2
sudo apt-get install postgresql
sudo apt install -y postgresql-common
psql --version
pg_lsclusters
sudo pg_ctlcluster 17 main start


sudo -u postgres psql
CREATE USER ecommerce WITH PASSWORD 'mypass';
CREATE DATABASE ecommerce OWNER ecommerce ENCODING 'UTF8';
\q
```

3. Установи резервную копию БД (при необходимости):

```sh
pg_restore -U ecommerce -h localhost -p 5433 -d ecommerce -v ecommerce.dump

```

- Создай резервную копию:
```sh
cd ./Desktop/MAI/e_com_proj/ecommerce 
pg_dump -U postgres -h localhost -p 5433 -F c -b -v -f ecommerce.dump ecommerce
```


4. Для входа в СУБД:

```sh
sudo psql -U ecommerce -h localhost -p 5433 -d ecommerce
```

5. Для запуска проекта из папки:

```sh
uvicorn app.main:app --reload
```

```
sudo lsof -i :8000
kill -9 
```

6. Данные для входа (логин, пароль):

- Админ
```
tng00 
5364 
```

- Покупатель
```
customer
customer
```

- Поставщик
```
supplier
supplier
```
