from django.db import models
from .validators import validate_file_extension
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.conf import settings

import os

class Enums:
    SIMULATION_TYPES = (
        ("Stand Alone Storage", "Stand Alone Storage"),
        ("PV + Storage", "PV + Storage"),
        ("Wind + Storage", "Wind + Storage"),
        ("Mobility Applications", "Mobility Applications")
    )

MODEL_INPUT_FILES = settings.MEDIA_ROOT + "/models/input/"
MODEL_OUTPUT_FILES = settings.MEDIA_ROOT +"/models/output/"

class Simulation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    project_name = models.CharField(max_length=255, unique=True, blank=True)
    project_description = RichTextField(blank=True)
    project_type = models.CharField(max_length=100, blank=True, choices=Enums.SIMULATION_TYPES, default=Enums.SIMULATION_TYPES[0][0])
    start = models.DateTimeField(blank=False)
    end = models.DateTimeField(blank=False)

    def __str__(self) -> str:
        return self.title

    @staticmethod
    def getPath(id, branch='inputs'):
        if branch=='inputs' or branch=='outputs':
            return f"{settings.MEDIA_ROOT}/{branch}/simul_{id:03d}"
        raise Exception("Simulation::getPath() Bad call")
    
    def createPaths(self):
        os.makedirs(Simulation.getPath(self.id, 'inputs'),exist_ok=True)
        os.makedirs(Simulation.getPath(self.id, 'outputs'),exist_ok=True)

    # def getInputFolder(self):
    #     return Simulation.getPath(self.id,'inputs')

def simulation_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/inputs/simulation_<id>/<filename>
    # return 'inputs/simulation_{0}/{1}'.format(instance.simulation.id, filename)
    return Simulation.getPath(instance.simulation.id, 'inputs')+'/'+filename

class SimulationInput(models.Model):
    input_file = models.FileField(upload_to=simulation_directory_path, blank=True, null=True, validators=[validate_file_extension])
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name="simulation_input", related_query_name="simulation_input", blank=True)