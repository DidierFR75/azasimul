# AzaSimul - Financial simulation

## Setup

```shell script
$ make
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
```

### Demo credentials

| Username | Email                 | Password      | Role  |
| -------- | --------------------- |:-------------:| ----- |
| admin    | admin@azasimul.fr     |  AzaPass999   | Admin |
| aza      | aza@azasimul.fr       |  AzaPass999   | User  |