from django.db import models

class Simulation(models.Model):
    # Project Properties
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=1000)
    type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Storage System & Requirements
    service_start = models.DateTimeField(null=True, blank=True)
    service_end = models.DateTimeField(null=True, blank=True)
    max_hours_of_sustained_output_required = models.IntegerField(null=True, blank=True)
    daily_need_usage = models.IntegerField(null=True, blank=True) # in MWh
    cycles_required_per_year = models.IntegerField(null=True, blank=True)

    # Market Assumptions
    wacc = models.FloatField(null=True, blank=True) # Weighted Average Cost of Capital
    annual_inflation_rate = models.FloatField(null=True, blank=True)
    cycle_life = models.FloatField(null=True, blank=True)
    
    # Cost of Energy to Charge

    annual_insurance_cost = models.FloatField(null=True, blank=True) # Opex in percentage of total cost