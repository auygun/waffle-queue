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
Python Virtual Environment for the packages.
```text
sudo pacman -S mariadb
sudo mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
sudo systemctl start mariadb.service
sudo mariadb
> ALTER USER 'mysql'@'localhost' IDENTIFIED BY 'mysql';
> CREATE DATABASE waffle_queue;

sudo pacman -S python-flask
sudo pacman -S python-pymysql
sudo pacman -S python-lazy-object-proxy
sudo pacman -S python-pyjwt

cd server
./sql_runner.py create_or_update_schema.sql

./webapp.py
```
(*Optional / Production*) Run with **gunicorn** and **gevent**.
The backend uses pymysql which is gevent friendly
(automatically gets monkey-patched).
```text
sudo pacman -S gunicorn
sudo pacman -S python-gevent

gunicorn -k gevent -w 4 -b 127.0.0.1:5001 'package.webapp.app:create_app()'
```
(*Optional / Production*) Put gunicorn behind a **nginx** HTTP proxy server.
```text
server {
    location /api/v1/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ...
}
```

### Run the scheduler daemon:
Scheduler puts build jobs in the queue for workers and integrates branches.
```text
cd server
./scheduler.py
```

### Run a worker daemon:
Workers pull and run build jobs from queue. Each worker takes a unique id as
argument.
```text
cd server
./worker.py 1
```

## Third-party software:
[vue](https://github.com/vuejs/),
[axios](https://github.com/axios/axios),
[simple.css](https://github.com/kevquirk/simple.css),
[material-icons](https://github.com/marella/material-icons),
[flask](https://github.com/pallets/flask/),
[pymysql](https://github.com/PyMySQL/PyMySQL),
[lazy-object-proxy](https://github.com/ionelmc/python-lazy-object-proxy),
[pyjwt](https://github.com/jpadilla/pyjwt),
[mariadb](https://github.com/MariaDB/server)