Install requirements:
sudo pacman -S python-aiosqlite
sudo pacman -S python-flask-cors
sudo pacman -S python-flask

Initialize db:
flask init-db

Run backend:
flask run --port=5001 --debug

Run frontend:
npm run dev