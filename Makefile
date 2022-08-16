SERVER=docker-compose exec web

# Démarre le serveur
run:
	docker-compose up --build -d

# Ferme le serveur
down:
	docker-compose down

# Relance le serveur
restart:
	make down
	make run

# Clean based install docker
refresh:
	docker stop $(docker ps -aq) && docker rm $(docker ps -aq)

# Ouvre le container de web
bash:
	$(SERVER) bash

migration:
	$(SERVER) python manage.py makemigrations
	$(SERVER) python manage.py migrate