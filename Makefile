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

# Génère un diagram des modèles du projet
graph:
	$(SERVER) python3 manage.py graph_models -a -g -o aza_graph_project.png

# Lance l'installation initiale du projet
install:
	# rm -rf data && rm -rf web/media && rm -rf web/simulator/migrations
	# mkdir web/simulator/migrations
	# touch web/simulator/migrations/__init__.py
	rm -rf data
	rm -rf web/simulator/migrations
	mkdir web/simulator/migrations
	touch web/simulator/migrations/__init__.py
	make
	chmod -R 777 data
	$(SERVER) python3 manage.py makemigrations
	sleep 20
	$(SERVER) python3 manage.py migrate
	make graph
	$(SERVER) python3 manage.py loaddata simulator/fixtures/users.json
	$(SERVER) python3 manage.py collectstatic --noinput
	make restart

django-shell:
	$(SERVER) python3 manage.py shell

tests:
	$(SERVER) python3 manage.py test tests/g