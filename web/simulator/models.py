from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from .validators import validate_file_extension
from ckeditor.fields import RichTextField

class Enums:
    UNIT = (
        (None, ''),
        ("W", "Watt"),
        ("$", "Dollar")
    )

    UNIT_SEPARATOR = (
        (None, 'Null'),
        ('/', 'By')
    )

    SIMULATION_TYPES = (
        ("sas", "Stand Alone Storage"),
        ("pvs", "PV + Storage"),
        ("ws", "Wind + Storage"),
        ("ma", "Mobility Applications")
    )

class Simulation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    title = models.CharField(max_length=255)
    description = RichTextField()
    type = models.CharField(max_length=100, choices=Enums.SIMULATION_TYPES, default=Enums.SIMULATION_TYPES[0][0])
    start = models.DateTimeField()
    end = models.DateTimeField()
    input_file = models.FileField(upload_to="inputs/", blank=True, null=True, validators=[validate_file_extension])
    #user = models.ForeignKey('User', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title

"""
    Define data entered by the user
"""
class BaseElement(models.Model):
    label = models.CharField(max_length=255)
    value = models.FloatField()
    unit = models.JSONField() #{'value1': UNIT, 'value2': UNIT }
    unit_separator = models.CharField(max_length=3, choices=Enums.UNIT_SEPARATOR, default=None)

"""
    Define a value of baseElement's values 
"""
class BaseElementValue(models.Model):
    base_element = models.ForeignKey(BaseElement, on_delete=models.CASCADE)

"""
    List all specification which are possible in the system
"""
class PossibleSpecification(models.Model):
    specification_name = models.CharField(max_length=255)
    functions_associate = models.JSONField() #{function_name: function_associate}
    functions_parameters = models.JSONField() # {parameter_name: variable_type}

"""
    Define calculation's rules of the system for a given Composition
"""
class Specification(models.Model):
    composition = models.ForeignKey('Composition', on_delete=models.CASCADE)
    specifications_possible = models.ManyToManyField(PossibleSpecification)


"""
    Define a composition of baseElements with its calculation's rules
"""
class Composition(models.Model):
    base_elements = models.ManyToManyField(BaseElement)