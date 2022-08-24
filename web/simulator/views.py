from django.shortcuts import render, redirect, get_object_or_404
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

from openpyxl import Workbook, load_workbook
from openpyxl.writer.excel import save_virtual_workbook
import os

from .forms import BaseElementForm, BaseCompositeForm, ElementForm, NewUserForm, OperationAvailableForm, SimulationForm
from .models import BaseElement, BaseComposite, Composite, Element, OperationAvailable, Simulation

def _addElementFromStructure(simulation:Simulation):
    """
    Copy the empty BaseStructure in the simulation structure
    """
    root = simulation.root_composition
    children = root.get_tree(parent=root)
    for child in children:
        composite = Composite(simulation=simulation, base_composition=child)
        composite.save()
        if child.base_elements is not None:
            for base_element in child.base_elements.all():
                element = Element.objects.filter(simulation=simulation, base_element=base_element, composition=composite)
                if not element.exists():
                    element = Element(simulation=simulation, base_element=base_element, composition=composite)
                    element.save()

@login_required(login_url="simulator:login")
def index(request):
    simulations = Simulation.objects.all()
    return render(request, "dashboard/index.html", {"simulations": simulations})

@login_required(login_url="simulator:login")
def new(request):
    if request.method == "POST":
        form = SimulationForm(request.POST, request.FILES)
        if form.is_valid():
            simulation = form.save()
            _addElementFromStructure(simulation)
            messages.success(request, "The simulation has been register !")
            return redirect("simulator:index")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)

    form = SimulationForm()
    return render(request, 'dashboard/new.html', {"simulation_form": form})

@login_required(login_url="simulator:login")
def detail(request, id):
    simulation = get_object_or_404(Simulation, id=id)
    return render(request, "dashboard/detail.html", {
        "simulation": simulation
    })

@login_required(login_url="simulator:login")
def edit(request, id):
    simulation = get_object_or_404(Simulation, id=id)
    if request.method == "POST":
        form = SimulationForm(request.POST, request.FILES, instance=simulation)
        if form.is_valid():
            form.save()
            messages.success(request, "The simulation has been register !")
            return redirect("simulator:index")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)
    
    form = SimulationForm(instance=simulation)
    return render(request, "dashboard/edit.html", {
        "edit_form": form,
        "simulation": simulation
        })
    
@login_required(login_url="simulation:login")
def delete(request, id):
    simulation = get_object_or_404(Simulation, id=id)
    simulation.delete()
    messages.success(request, 'The simulation '+simulation.title+' has been deleted')
    return redirect('simulator:index')

@login_required(login_url='simulation:login')
def generateCSV(request, id):
    simulation = get_object_or_404(Simulation, id=id)
    
    ws = load_workbook(os.getcwd()+ "/simulator/outputs/simplified.xlsx")

    columns = {
        "Project Type": simulation.type, 
        "Project Name": simulation.title, 
        "Project Description": simulation.description, 
        "Model creation date": "", 
        "Nameplate Load": "", 
        "Battery Capacity Degredation per Annum": "",
        "Hours of Sustained Output": "",
        "Cycle Need Usage": "", 
        "Cycles Required per Year": "", 
        }
    
    i=3
    for key, value in columns.items():
        ws.cell(column="F", row=i, value=value)
        i = i+1

    response = HttpResponse(content=save_virtual_workbook(ws), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=myexport.xlsx'
    return response

# BaseComposite Pages
@login_required(login_url="simulator:login")
def index_composite(request):
    compositions = BaseComposite.objects.all()
    return render(request, "base_composite/index.html", {"compositions": compositions})

@login_required(login_url="simulator:login")
def new_composite(request):
    if request.method == "POST":
        form = BaseCompositeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "The composition has been register !")
            return redirect("simulator:index_composite")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)

    form = BaseCompositeForm()
    return render(request, 'base_composite/new.html', {"composite_form": form})

@login_required(login_url="simulator:login")
def detail_composite(request, id):
    composition = get_object_or_404(BaseComposite, id=id)
    return render(request, "base_composite/detail.html", {
        "composition": composition
    })

@login_required(login_url="simulator:login")
def edit_composite(request, id):
    composition = get_object_or_404(BaseComposite, id=id)
    if request.method == "POST":
        form = BaseCompositeForm(request.POST, instance=composition)
        if form.is_valid():
            form.save()
            messages.success(request, "The composition has been register !")
            return redirect("simulator:index_composite")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)
    
    form = BaseCompositeForm(instance=composition)
    return render(request, "base_composite/edit.html", {
        "edit_form": form,
        "composition": composition
        })
    
@login_required(login_url="simulation:login")
def delete_composite(request, id):
    composition = get_object_or_404(BaseComposite, id=id)
    composition.delete()
    messages.success(request, 'The simulation '+composition.label+' has been deleted')
    return redirect('simulator:index_composite')

# Elements Pages
@login_required(login_url="simulator:login")
def index_element(request):
    elements = Element.objects.all()
    return render(request, "element/index.html", {"elements": elements})

@login_required(login_url="simulator:login")
def new_element(request):
    if request.method == "POST":
        form = ElementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "The element has been register !")
            return redirect("simulator:index_element")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)

    form = ElementForm()
    return render(request, 'element/new.html', {"element_form": form})

@login_required(login_url="simulator:login")
def detail_element(request, id):
    element = get_object_or_404(Element, id=id)
    return render(request, "element/detail.html", {
        "element": element
    })

@login_required(login_url="simulator:login")
def edit_element(request, id):
    element = get_object_or_404(Element, id=id)
    if request.method == "POST":
        form = ElementForm(request.POST, instance=element)
        if form.is_valid():
            form.save()
            messages.success(request, "The element has been register !")
            return redirect("simulator:index_element")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)
    
    form = ElementForm(instance=element)
    return render(request, "element/edit.html", {
        "element_form": form,
        "element": element
        })
    
@login_required(login_url="simulation:login")
def delete_element(request, id):
    element = get_object_or_404(Element, id=id)
    element.delete()
    messages.success(request, 'The element has been deleted')
    return redirect('simulator:index_element')

# BaseElements Pages
@login_required(login_url="simulator:login")
def index_base_element(request):
    base_elements = BaseElement.objects.all()
    return render(request, "base_element/index.html", {"base_elements": base_elements})

@login_required(login_url="simulator:login")
def new_base_element(request):
    if request.method == "POST":
        form = BaseElementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "The element has been register !")
            return redirect("simulator:index_base_element")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)

    form = BaseElementForm()
    return render(request, 'base_element/new.html', {"base_element_form": form})

@login_required(login_url="simulator:login")
def detail_base_element(request, id):
    base_element = get_object_or_404(BaseElement, id=id)
    return render(request, "base_element/detail.html", {
        "base_element": base_element
    })

@login_required(login_url="simulator:login")
def edit_base_element(request, id):
    base_element = get_object_or_404(BaseElement, id=id)
    if request.method == "POST":
        form = BaseElementForm(request.POST, instance=base_element)
        if form.is_valid():
            form.save()
            messages.success(request, "The element has been register !")
            return redirect("simulator:index_base_element")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)
    
    form = BaseElementForm(instance=base_element)
    return render(request, "base_element/edit.html", {
        "base_element_form": form,
        "base_element": base_element
        })
    
@login_required(login_url="simulation:login")
def delete_base_element(request, id):
    base_element = get_object_or_404(BaseElement, id=id)
    base_element.delete()
    messages.success(request, 'The simulation '+base_element.label+' has been deleted')
    return redirect('simulator:index_base_element')

# Operations available Pages
@login_required(login_url="simulator:login")
def index_operations_available(request):
    operations = OperationAvailable.objects.all()
    return render(request, "operation_available/index.html", {"operations": operations})

@login_required(login_url="simulator:login")
def new_operation_available(request):
    if request.method == "POST":
        form = OperationAvailableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "The operation avaible has been register !")
            return redirect("simulator:index_operations_available")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)

    form = OperationAvailableForm()
    return render(request, 'operation_available/new.html', {"operation_available_form": form})

@login_required(login_url="simulator:login")
def detail_operation_available(request, id):
    operation_available = get_object_or_404(OperationAvailable, id=id)
    return render(request, "operation_available/detail.html", {
        "base_element": operation_available
    })

@login_required(login_url="simulator:login")
def edit_operation_available(request, id):
    operation_available = get_object_or_404(OperationAvailable, id=id)
    if request.method == "POST":
        form = BaseElementForm(request.POST, instance=operation_available)
        if form.is_valid():
            form.save()
            messages.success(request, "The operation has been register !")
            return redirect("simulator:index_operations_available")
        
        message = ""
        if form.errors:
            for field in form:
                for error in field.errors:
                    message = message + error + ', '
        messages.error(request, "An error appear : " + message)
    
    form = BaseElementForm(instance=operation_available)
    return render(request, "operation_available/edit.html", {
        "operation_available_form": form,
        "operation_available": operation_available
        })
    
@login_required(login_url="simulation:login")
def delete_operation_available(request, id):
    operation_available = get_object_or_404(OperationAvailable, id=id)
    operation_available.delete()
    messages.success(request, 'The simulation '+operation_available.label+' has been deleted')
    return redirect('simulator:index_operation_available')

# User Pages
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

@login_required(login_url="simulator:login")
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