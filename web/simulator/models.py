from django.db import models
from .validators import validate_file_extension
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User

class Enums:
    SIMULATION_TYPES = (
        ("Stand Alone Storage", "Stand Alone Storage"),
        ("PV + Storage", "PV + Storage"),
        ("Wind + Storage", "Wind + Storage"),
        ("Mobility Applications", "Mobility Applications")
    )

# Simulations and their Elements
class Simulation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    project_name = models.CharField(max_length=255, unique=True, blank=True)
    project_description = RichTextField(blank=True)
    project_type = models.CharField(max_length=100, blank=True, choices=Enums.SIMULATION_TYPES, default=Enums.SIMULATION_TYPES[0][0])
    start = models.DateTimeField(blank=True)
    end = models.DateTimeField(blank=True)

    def __str__(self) -> str:
        return self.title

    def getInputFolder(self):
        return "inputs/simulation_{}".format(self.id)

def simulation_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/inputs/simulation_<id>/<filename>
    return 'inputs/simulation_{0}/{1}'.format(instance.simulation.id, filename)

class SimulationInput(models.Model):
    input_file = models.FileField(upload_to=simulation_directory_path, blank=True, null=True, validators=[validate_file_extension])
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name="simulation_input", related_query_name="simulation_input", blank=True)