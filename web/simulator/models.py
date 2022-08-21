from secrets import choice
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from .validators import validate_file_extension
from ckeditor.fields import RichTextField

from treebeard.mp_tree import MP_Node
from abc import ABCMeta, abstractmethod

class Enums:
    UNIT = (
        (None, ''),
        ("W", "Watt"),
        ("$", "Dollar"),
        ("V", "Volt")
    )

    UNIT_SEPARATOR = (
        (None, 'Null'),
        ('/', 'By')
    )

    CURVES = (
        (None, ''),
        ("const", "Constant"),
        ("linear", "Linear"),
        ("log", "Logarithmic"),
        ("exp", "exponential"),
    )

    SIMULATION_TYPES = (
        ("sas", "Stand Alone Storage"),
        ("pvs", "PV + Storage"),
        ("ws", "Wind + Storage"),
        ("ma", "Mobility Applications")
    )

# Composite Design Pattern for model's values

class BaseElement(models.Model):
    """
    The BaseElement class represents the end objects of a composition. A BaseElement can't
    have any children. It's the Leaf objects that do the actual work, whereas Composite
    objects only delegate to their sub-components.
    """

    label = models.CharField(max_length=255)
    unit = models.CharField(max_length=30, choices=Enums.UNIT, default=None)
    curve_interpolation = models.CharField(max_length=30, choices=Enums.CURVES, default=Enums.CURVES[0][0])
    date = models.DateTimeField()
    quantity = models.PositiveIntegerField()
    value = models.CharField(max_length=255)

    def sumByUnit(self, unit):
        result = 0
        if self.unit == unit:
            for value in self.values:
                result = result + (value["quantity"] * value["value"])
        return result

class Composite(MP_Node):
    """
    The Composite class represents the complex components that may have
    children. The Composite objects delegate the actual work to their
    children and then "sum-up" the result.
    """
    node_order_by = ['label']

    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    base_elements = models.ManyToManyField(BaseElement, blank=True) # if no child

    def __str__(self) -> str:
        return 'Composition : {}'.format(self.label)

    def sumByUnit(self, unit):
        leafs = self.base_elements if self.base_elements is not None else []
        return sum([leaf.sumByUnit(unit) for leaf in leafs])

# Simulations models
class Simulation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    title = models.CharField(max_length=255)
    description = RichTextField()
    type = models.CharField(max_length=100, choices=Enums.SIMULATION_TYPES, default=Enums.SIMULATION_TYPES[0][0])
    start = models.DateTimeField()
    end = models.DateTimeField()
    input_file = models.FileField(upload_to="inputs/", blank=True, null=True, validators=[validate_file_extension])
    composition = models.OneToOneField(Composite, on_delete=models.CASCADE) # if it's root

    def __str__(self) -> str:
        return self.title

""" 
class BaseElement(models.Model):
    label = models.CharField(max_length=255)
    value = models.FloatField()
    unit = models.JSONField() #{'value1': UNIT, 'value2': UNIT }
    unit_separator = models.CharField(max_length=3, choices=Enums.UNIT_SEPARATOR, default=None)

class BaseElementValue(models.Model):
    base_element = models.ForeignKey(BaseElement, on_delete=models.CASCADE)

class PossibleSpecification(models.Model):
    specification_name = models.CharField(max_length=255)
    functions_associate = models.JSONField() #{function_name: function_associate}
    functions_parameters = models.JSONField() # {parameter_name: variable_type}

class Specification(models.Model):
    composition = models.ForeignKey('Composition', on_delete=models.CASCADE)
    specifications_possible = models.ManyToManyField(PossibleSpecification)

"""