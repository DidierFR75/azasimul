# AzaSimul - Financial simulation

## Setup

```shell script
$ make && make install
```

Website on localhost:8000

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
```

### Demo credentials

| Username | Email                 | Password      | Role  |
| -------- | --------------------- |:-------------:| ----- |
| admin    | admin@azasimul.fr     |  AzaPass999   | Admin |
| aza      | aza@azasimul.fr       |  AzaPass999   | User  |