from rest_framework import serializers
from .models import BaseElement, BaseElementValue, PossibleSpecification, Specification, Composition

class BaseElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseElement
        fields = '__all__'

class BaseElementValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseElementValue
        fields = '__all__'

class PossibleSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PossibleSpecification
        fields = '__all__'

class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = '__all__'

class CompositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Composition
        fields = '__all__'