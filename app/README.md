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

## Решение проблемы 10к соединений:


### 1. Используем один uvicorn worker:


```sh
uvicorn app.main:app --reload
```

- Результат:
Сервер обрабатывает 207 запросов в секунду в среднем, что довольно низко для производительности веб-приложения.
Это итоговая производительность, что говорит о том, что за 30 секунд было обработано 3664 запроса.
```
snowwy@snowwy-BOM-WXX9:~$ wrk -t4 -c100 -d30s http://127.0.0.1:8000/
Running 30s test @ http://127.0.0.1:8000/
  4 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    38.51ms  100.73ms   1.87s    98.18%
    Req/Sec     0.92k   207.04     1.26k    76.67%
  110040 requests in 30.03s, 13.43MB read
Requests/sec:   3664.17
Transfer/sec:    458.02KB
```

### 2. Используем больше uvicorn workers (success):

- Число воркеров = число ядер CPU * 2 — оптимальное соотношение.
```sh

uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

- Результат:
Сервер теперь обрабатывает почти 600 запросов в секунду, что указывает на улучшение производительности.
Итоговая пропускная способность выросла до 11842 запросов в секунду, что значительно лучше.

```
snowwy@snowwy-BOM-WXX9:~$ wrk -t4 -c100 -d30s http://127.0.0.1:8000/
Running 30s test @ http://127.0.0.1:8000/
  4 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     8.56ms    3.76ms  88.96ms   81.69%
    Req/Sec     2.98k   599.60     3.96k    63.83%
  355687 requests in 30.04s, 43.42MB read
Requests/sec:  11842.11
Transfer/sec:      1.45MB
```


### 3. Используем gunicorn с тем же числом workers (success):

```sh
which python
which pip
export PYTHONPATH=$PYTHONPATH:/home/snowwy/Desktop/MAI/e_com_proj/ecommerce/.venv/lib/python3.10/site-packages
sudo apt install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```


- Результат:
Сервер теперь обрабатывает почти 981 запрос в секунду в среднем.
```
snowwy@snowwy-BOM-WXX9:~$ wrk -t4 -c100 -d30s http://127.0.0.1:8000/
Running 30s test @ http://127.0.0.1:8000/
  4 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     4.31ms    1.72ms  60.31ms   80.74%
    Req/Sec     5.86k     0.96k    7.37k    61.58%
  699480 requests in 30.01s, 85.39MB read
Requests/sec:  23306.18
Transfer/sec:      2.84MB
snowwy@snowwy-BOM-WXX9:~$ 
```

Судя по результатам последнего теста, проблема 10,000 запросов в секунду решена. Сервер показывает пропускную способность 23,306 запросов в секунду при средней задержке 4.31 мс, что более чем достаточно для обработки 10к запросов.

## 4. Load Balancing:

- Использование балансировщика нагрузки (например, Nginx).
- Это распределит нагрузку между несколькими инстансам FastAPI-приложения.

## 5. Caching:
- Если запросы часто повторяются, можно использовать кэш (Redis, Memcached) для ускорения ответа, что актуально для recsys.


## 6. Async queue:
- Для длительных операций подойдет Celery или аналогичный инструмент.

