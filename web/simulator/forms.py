from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import BaseElement, Composite, Simulation
from treebeard.forms import MoveNodeForm

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user

class SimulationForm(forms.ModelForm):
	class Meta:
		model = Simulation
		fields = '__all__'
		exclude = ('created_at', "updated_at")
		
	def __init__(self, *args, **kwargs):
		super(SimulationForm, self).__init__(*args, **kwargs)
		self.fields['input_file'].required = False

class CompositeForm(MoveNodeForm):
    class Meta:
        model = Composite
        exclude = ('sib_order', 'parent', "path", "depth", "numchild")

class BaseElementForm(forms.ModelForm):
	class Meta:
		model = BaseElement
		fields = '__all__'
		exclude = ('created_at', "updated_at")
