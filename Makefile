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

# Execute des migrations
migration:
	$(SERVER) python3 manage.py makemigrations
	$(SERVER) python3 manage.py migrate

# Lance l'installation initiale du projet
install:
	make migration
	$(SERVER) python3 manage.py loaddata simulator/fixtures/*.json

# Génère un diagram des modèles du projet
graph:
	$(SERVER) python3 manage.py graph_models -a -g -o aza_graph_project.png