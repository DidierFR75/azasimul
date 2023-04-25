from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Simulation
from django.forms import ClearableFileInput

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
		exclude = ('created_at', "updated_at", "user", "start", "end")
		widgets = {
            'input_files': ClearableFileInput(attrs={'multiple': True})
        }
