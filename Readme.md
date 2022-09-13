# AzaSimul - Financial simulation

## Demo

You can find the app on http://aza.masterbrain.fr:8000 and the Jenkins interface on http://aza.masterbrain.fr:8080 

## Setup

```shell script
$ make && make install
```

## Documentation

You can find the app on http://localhost:8000 and the Jenkins interface on http://localhost:8080 

### Dev shortcuts

Util commands for development:
```shell script
$ make         # launch server
$ make install # Create db and load fixtures
$ make down    # Shutdown server
$ make restart # Restart server
$ make refresh # Reload container based files
$ make bash    # Run serveur terminal for debugging
$ make migration # Execute model's migrations in Django
$ make graph # Generate the entire graph of the system at web/aza_graph_project.png
$ make django-shell # Access to django shell admin
$ make tests # Run unit tests
$ make deploy # Deploy the project to the production server
$ make help # Display description of all commands
```

### Demo credentials

| Username | Email                 | Password      | Role  |
| -------- | --------------------- |:-------------:| ----- |
| admin    | admin@azasimul.fr     |  AzaPass999   | Admin |
| aza      | aza@azasimul.fr       |  AzaPass999   | User  |


### Deployment

```shell script
$ make deploy
```

### Input file format


### Output file format