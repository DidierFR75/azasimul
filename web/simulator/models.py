from tokenize import blank_re
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from .validators import validate_file_extension
from ckeditor.fields import RichTextField

from treebeard.mp_tree import MP_Node
from abc import ABCMeta, abstractmethod

class Enums:
    UNIT = (
        (None, 'No unit'),
        ("W", "Watt"),
        ("$", "Dollar"),
        ("V", "Volt"),
        ("%", "Percentage"),
        ("Ah", "Ampere hour")
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

# Composite Design Pattern for engine representation

class OperationAvailable(MP_Node):
    """
    Define the tree of all possible operations for a composite and its BaseElements
    """
    label = models.CharField(max_length=255)
    function_associate = models.CharField(max_length=255)
    parameters = models.JSONField() # {compositions.spec|base_element}

class BaseElement(models.Model):
    label = models.CharField(max_length=255, unique=True)
    unit = models.CharField(max_length=30, choices=Enums.UNIT, default=None)
    description = RichTextField(blank=True, null=True, default=None)

    def __str__(self) -> str:
        return "{} ({})".format(self.label, self.unit)

class BaseComposite(MP_Node):
    """
    The Composite class represents the complex components that may have
    children. The Composite objects delegate the actual work to their
    children and then "sum-up" the result.
    """
    node_order_by = ['label']

    label = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True, default=None)
    base_elements = models.ManyToManyField(BaseElement, blank=True)
    operations_available = models.ManyToManyField(OperationAvailable, blank=True)
    
    def __str__(self) -> str:
        return 'Composition : {}'.format(self.label)

# Simulations and their Elements
class Simulation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    title = models.CharField(max_length=255, unique=True)
    description = RichTextField()
    type = models.CharField(max_length=100, choices=Enums.SIMULATION_TYPES, default=Enums.SIMULATION_TYPES[0][0])
    start = models.DateTimeField()
    end = models.DateTimeField()
    input_file = models.FileField(upload_to="inputs/", blank=True, null=True, validators=[validate_file_extension])
    root_composition = models.ForeignKey(BaseComposite, on_delete=models.CASCADE) # Each simulation is associate to the root composition

    def __str__(self) -> str:
        return self.title

class Composite(models.Model):
    """
    The Composite class represents the complex components that may have
    children. The Composite objects delegate the actual work to their
    children and then "sum-up" the result.
    """
    
    quantity = models.PositiveIntegerField(null=True, blank=True, default=None)
    additional_informations = models.JSONField(null=True, blank=True, default=None) # for information only
    
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
    base_composition = models.ForeignKey(BaseComposite, on_delete=models.CASCADE)

class Element(models.Model):
    """
    The BaseElement class represents the end objects of a composition. A BaseElement can't
    have any children. It's the Leaf objects that do the actual work, whereas Composite
    objects only delegate to their sub-components.
    """
    date = models.DateField(null=True, blank=True, default=None)
    value = models.CharField(max_length=255, null=True, blank=True, default=None)
    quantity = models.PositiveIntegerField(null=True, blank=True, default=None)
    additional_informations = models.JSONField(null=True, blank=True, default=None) # for information only

    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
    base_element = models.ForeignKey(BaseElement, on_delete=models.CASCADE)
    composition = models.ForeignKey(Composite, on_delete=models.CASCADE)

class Operation(models.Model):
    label = models.CharField(max_length=255, unique=True)
    operation_available = models.ForeignKey(OperationAvailable, on_delete=models.CASCADE)
    unit = models.CharField(max_length=30, choices=Enums.UNIT, default=None)
    parameters = models.JSONField(null=True, blank=True, default=None) # {base_element_label_1: param_position_1, base_element_label_2: param_position_2, ...}
