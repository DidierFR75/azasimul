from django.shortcuts import render, redirect
from .forms import NewUserForm, SimulationForm
from .serializers import BaseElementSerializer, BaseElementValueSerializer, PossibleSpecificationSerializer, SpecificationSerializer, CompositionSerializer
from .models import BaseElement, BaseElementValue, PossibleSpecification, Specification, Composition
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from rest_framework import serializers

def form_simulation(request):
    if request.method == 'POST':
        form = SimulationForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            return render(request, 'form/simulation.html', { 'form': form })
    elif request.method == 'GET':
        form = SimulationForm()
        return render(request, 'form/simulation.html', { 'form': form })

def form_elements(request):
    return render(request, 'form/elements.html')

class BaseElementView(viewsets.ModelViewSet):
    serializer_class = BaseElementSerializer
    queryset = BaseElement.objects.all()

class BaseElementValueView(viewsets.ModelViewSet):
    serializer_class = BaseElementValueSerializer
    queryset = BaseElementValue.objects.all()

    def get_queryset(self):
        base_element = self.request.query_params.get('base_element', None)
        if base_element:
            return BaseElementValue.objects.filter(base_element__pk = base_element)
        return super().get_queryset()

class PossibleSpecificationView(viewsets.ModelViewSet):
    serializer_class = PossibleSpecificationSerializer
    queryset = PossibleSpecification.objects.all()

class SpecificationView(viewsets.ModelViewSet):
    serializer_class = SpecificationSerializer
    queryset = Specification.objects.all()

class CompositionView(viewsets.ModelViewSet):
    serializer_class = CompositionSerializer
    queryset = Composition.objects.all()


@login_required(login_url="simulator:login")
def index(request):
    return render(request, 'dashboard/index.html', {})


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("simulator:index")

        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '

        messages.error(request, "Unsuccessful registration. " + message)
    form = NewUserForm()
    return render (request=request, template_name="users/register.html", context={"register_form": form})

def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.info(request, f"You are now logged in as {username}.")
				return redirect("simulator:index")
			else:
				messages.error(request,"Invalid username or password.")
		else:
			messages.error(request,"Invalid username or password.")
	form = AuthenticationForm()
	return render(request=request, template_name="users/login.html", context={"login_form": form})

def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect("simulator:index")

def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "users/password/password_reset_email.txt"
                    c = {
                    "email":user.email,
                    'domain':'127.0.0.1:8000',
                    'site_name': 'Website',
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, 'admin@example.com' , [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    messages.success(request, 'A message with reset password instructions has been sent to your inbox.')
                    return redirect ("simulator:index")
            messages.error(request, "An invalid email has been entered")
        messages.error(request, "This user email doesn't exist")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="users/password/password_reset.html", context={"password_reset_form": password_reset_form})