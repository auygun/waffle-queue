# WaffleQueue

My personal CI/CD project. Uses Vue for the frontend, Flask and MariaDB for the
backend. This project is work-in-progress and still in its infancy.

## Client:

### Install requirements and run the frontend:
```text
cd client
npm install

npm run dev
```

## Server:

### Install requirements and run the backend:
The following steps are for Arch Linux. Alternatively pip can be used in a
Python virtual environment for the packages.
```text
sudo pacman -S mariadb

sudo pacman -S python-flask
sudo pacman -S python-pymysql
sudo pacman -S python-aiomysql
sudo pacman -S python-lazy-object-proxy

cd server
./sql_runner.py create_db.sql

cd webapp
./app.py
```
(*Optional / Production*) Run with **gunicorn** and **gevent**.
The backend uses pymysql which is gevent friendly
(automatically gets monkey-patched)
```text
sudo pacman -S gunicorn
sudo pacman -S python-gevent

gunicorn -k gevent -w 4 -b 127.0.0.1:5001 'app:create_app()'
```
(*Alternative option*) Use **gthread** asynchronous worker class:
```
gunicorn --threads 5 -w 4 -b 127.0.0.1:5001 'app:create_app()'
```
(*Optional / Production*) Put gunicorn behind a **nginx** HTTP proxy server:
```text
    location /api/v1/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
```

### Run the worker daemon:
Workers pull and run build jobs from queue.
```text
cd server/worker
./worker_daemon.py
```

## Third-party software:
[vue](https://github.com/vuejs/),
[axios](https://github.com/axios/axios),
[pinia](https://github.com/vuejs/pinia),
[simple.css](https://github.com/kevquirk/simple.css),
[material-icons](https://github.com/marella/material-icons),
[flask](https://github.com/pallets/flask/),
[aiomysql](https://github.com/aio-libs/aiomysql),
[pymysql](https://github.com/PyMySQL/PyMySQL),
[pymysql-pool](https://github.com/jkklee/pymysql-pool),
[mariadb](https://github.com/MariaDB/server)