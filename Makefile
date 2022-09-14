.PHONY: deploy

# Environnement's variables
SERVER=docker-compose run web
PRODUCTION_SERVER_ADDRESS=ubuntu@146.59.237.34

# Display Colors
COM_COLOR   = \033[0;34m
OBJ_COLOR   = \033[0;36m
OK_COLOR    = \033[0;32m
ERROR_COLOR = \033[0;31m
WARN_COLOR  = \033[0;33m
NO_COLOR    = \033[m

# -------------------------------------------------------------------------

run: ## Start server
	docker-compose up --build -d

down: ## Close server
	docker-compose down

restart: ## Restart server
	make down
	make run

refresh: ## Clean based install docker
	docker stop $(docker ps -aq) && docker rm $(docker ps -aq)

bash: ## Open web container
	$(SERVER) bash

migration: ## Execute migrations
	$(SERVER) python3 manage.py makemigrations
	$(SERVER) python3 manage.py migrate

graph: ## Generate model's diagram
	$(SERVER) python3 manage.py graph_models -a -g -o aza_graph_project.png

install: ## Init data's project
	# rm -rf data && rm -rf web/media && rm -rf web/simulator/migrations
	# mkdir web/simulator/migrations
	# touch web/simulator/migrations/__init__.py
	rm -rf data
	rm -rf web/simulator/migrations
	mkdir web/simulator/migrations
	mkdir web/media/models
	touch web/simulator/migrations/__init__.py
	make
	sleep 10
	chmod -R 777 data
	make migration
	make graph
	$(SERVER) python3 manage.py loaddata simulator/fixtures/users.json
	$(SERVER) python3 manage.py collectstatic --noinput
	make restart

django-shell: ## Open django shell
	$(SERVER) python3 manage.py shell

tests: ## Launch unit tests
	$(SERVER) python3 manage.py test tests/

install-prod: ## Install system in production
	$(SERVER) python3 manage.py makemigrations
	$(SERVER) python3 manage.py migrate
	$(SERVER) python3 manage.py loaddata simulator/fixtures/users.json
	$(SERVER) python3 manage.py collectstatic --noinput
	make restart

deploy: ## Deploy on production server
	@echo -e "\n$(WARN_COLOR)- Deploy the $(WARN_COLOR)sources$(WARN_COLOR) of $(ERROR_COLOR)production server$(NO_COLOR)\n"
	@ssh $(PRODUCTION_SERVER_ADDRESS) "sudo rm -rf azasimul"
	@rsync -auv \
	--exclude '/web/media' \
	--exclude '/jenkins' \
	--exclude '.gitignore' \
	--exclude '.git' \
	--exclude '/data' \
	. $(PRODUCTION_SERVER_ADDRESS):~/azasimul
	@echo -e "\n$(WARN_COLOR)- Start $(WARN_COLOR)the $(WARN_COLOR) prod $(ERROR_COLOR)server$(NO_COLOR)\n"
	@ssh $(PRODUCTION_SERVER_ADDRESS) "cd azasimul && make && rm -rf data && rm -rf web/simulator/migrations && mkdir web/simulator/migrations && touch web/simulator/migrations/__init__.py && mkdir web/media/models && make && sleep 10 && sudo chmod -R 777 . && sudo chmod -R 777 data && make install-prod"

help: ## Display the description of each action 
	@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-15s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'
