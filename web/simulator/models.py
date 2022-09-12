from django.db import models
from .validators import validate_file_extension
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User

class Enums:
    SIMULATION_TYPES = (
        ("sas", "Stand Alone Storage"),
        ("pvs", "PV + Storage"),
        ("ws", "Wind + Storage"),
        ("ma", "Mobility Applications")
    )

# Simulations and their Elements
class Simulation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=255, unique=True)
    description = RichTextField()
    type = models.CharField(max_length=100, choices=Enums.SIMULATION_TYPES, default=Enums.SIMULATION_TYPES[0][0])
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self) -> str:
        return self.title

    def getInputFolder(self):
        return "inputs/simulation_{}".format(self.id)

def simulation_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/inputs/simulation_<id>/<filename>
    return 'inputs/simulation_{0}/{1}'.format(instance.simulation.id, filename)

class SimulationInput(models.Model):
    input_file = models.FileField(upload_to=simulation_directory_path, blank=True, null=True, validators=[validate_file_extension])
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name="input_files")
