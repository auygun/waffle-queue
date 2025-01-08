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
The following steps are for Arch Linux. Alternatively "pip" can be used in a
Python virtual environment for the packages.
```text
sudo pacman -S mariadb

sudo pacman -S python-flask
sudo pacman -S python-pymysql
sudo pacman -S python-aiomysql
sudo pacman -S python-lazy-object-proxy

cd server
./sql_runner.py create_db.sql

./app.py
```

### Run the worker daemon:
```text
cd server
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
[mariadb](https://github.com/MariaDB/server)