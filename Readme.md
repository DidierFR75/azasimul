# AzaSimul - Financial simulation

## Demo

The demo is available on http://aza.masterbrain.fr:8000 and the Jenkins interface on http://aza.masterbrain.fr:8080 

## Setup

You must have the Docker Deamon running on your machine.

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

# Data importation

## Specifications and Summary

You can put the essential information of the project in an excel sheet with the name: **summary**
The system will consider that the first column corresponds to the name of an expected field and the following column will correspond to the value of this field.


## Models

All models are stored in web/media/models and can be downloaded via the web interface at http://localhost:8000/new_co

### Input Model (Operations and Constants)

These templates define the default constants and operations for a simulation.
If the specification files already have one of these operations, then it will be ignored and calculated as defined by the user.

The **constants** have the following format :

| Constant Category | Constant name | Value  | Unit  |
| ----------------- | ------------- |:------:| ----- |
| Dimensions        | Length        |  9.1   | cm    |

The **operations** have the following format:

| Composition name  | Operation name                   | Operation definition                                                 | Unit  |
| ----------------- | -------------------------------- |:--------------------------------------------------------------------:| ----- |
| Cell              | Nominal Capacity                 | { Weight } * [Energy Density (gravimetric)]                          | Wh    |
| BatteryPack       | Width                            | [Cell Quantity]*[Casing.Cell interspace]*[Cell.Width]+[Casing.Width] | mm    |
| BatteryPack       | Volume Overhead (Packs vs Cells) | {Cell.Energy density (volumetric)}/{Energy density (volumetric)}-1   |       |

Variables are defined by [name] and represent a specification to be provided by the user, [Composition_name.name] represents a variable present in Composition_name.

Functions are defined by {name} and represent a previously defined function in the current composition, {Composition_name.name} represents a function defined in Composition_name.

The **filters** have the following format:

Nous pouvons également ajouter des filtres aux paramètres de fonction nécessitant une transformation :

| Filter unit | Filter name  | Filter function               |
| ------------| ------------ |:-----------------------------:|
| date        | Year         | Show the year of date         |
| date        | Month        | Show the month of date        |
| date        | Day          | Show the day of date          |

### Output Model

To define a value to display in the model, you just have to add a value such as [Composition_name/Function_name.name] in a cell and it will be automatically replaced by the system if it exists.

Le mot clef for peut être ajouté afin d'afficher tous les points de la matrice de référence