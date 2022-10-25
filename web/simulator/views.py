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
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.http import Http404

from .forms import NewUserForm, SimulationForm
from .models import Simulation, SimulationInput
from .interpreter import FileChecker, SheetOutputGenerator, SheetInterpreter

import os
import zipfile
import shutil

MODEL_INPUT_FILES = settings.MEDIA_ROOT + "/models/input/"
MODEL_OUTPUT_FILES = settings.MEDIA_ROOT +"/models/output/"

@login_required(login_url="simulator:login")
def index(request):
    simulations = Simulation.objects.all()
    return render(request, "dashboard/index.html", {"simulations": simulations})

@login_required(login_url="simulator:login")
def new(request):
    if request.method == "POST":
        form = SimulationForm(request.POST, request.FILES)
        if form.is_valid():
            # Add current User in request
            simulation = form.save(commit=False)
            simulation.user = request.user
            
            # Files Handler
            files = request.FILES.getlist('input_files')
            inputs = []
            for f in files:
                # Temporary save file
                path = settings.MEDIA_ROOT+"/tmp/"+str(f)
                default_storage.save(path, ContentFile(f.read()))
                # Check if file has specification format or if it has summary sheet
                fc = FileChecker(path)
                fc.checkForSpecFormat()
                os.remove(path)

                # Add additionnal data in simulation
                if fc.summary is not None:
                    for summary in fc.summary:
                        summary["summary_name"] = summary["summary_name"].lower().replace(" ", "_")
                        if hasattr(simulation, summary["summary_name"]) and (getattr(simulation, summary["summary_name"]) is None or getattr(simulation, summary["summary_name"]) != summary["summary_value"]):
                            setattr(simulation, summary["summary_name"], summary["summary_value"])

                if fc.non_accepted != []:
                    messages.error(request, "The following sheets was not take into account : "+ ','.join(fc.non_accepted))

                # Create file object
                inputs.append(SimulationInput(input_file=f))
            
            # Create simulation object and inputs objects
            simulation.save()
            
            for input in inputs:
                input.simulation = simulation
                input.save()

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
def edit(request, id):
    simulation = get_object_or_404(Simulation, id=id)
    if request.method == "POST":
        form = SimulationForm(request.POST, request.FILES, instance=simulation)
        if form.is_valid():
            form.save()
             # Files Handler
            files = request.FILES.getlist('input_files')
            # Delete previous inputs
            if len(files) > 0:
                simulation.simulation_input.all().delete()
            # Add new inputs
            for f in files:
                SimulationInput.objects.create(input_file=f, simulation=simulation)

            messages.success(request, "The simulation has been modify !")
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
    messages.success(request, 'The simulation '+simulation.project_name+' has been deleted')
    return redirect('simulator:index')

@login_required(login_url='simulation:login')
def generateCSV(request, id):
    simulation = get_object_or_404(Simulation, id=id) 

    input_files = os.getcwd()+ "/media/"+simulation.getInputFolder()+"/"
    result_path = settings.MEDIA_ROOT+ "/outputs/simulation_{}/".format(simulation.id)

    # Copy /operations in media/input/simulation_id to take into account default operations
    for model_file in os.listdir(MODEL_INPUT_FILES):
        src = MODEL_INPUT_FILES + model_file
        dst = input_files + model_file
        shutil.copyfile(src, dst)

    # Generate output files
    output = SheetOutputGenerator(input_files, MODEL_OUTPUT_FILES)
    zip_path = output.generate(result_path, "simulation")
    
    # Zip all output file and serves to download
    zip_file = open(zip_path, 'rb')
    response = HttpResponse(zip_file, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="simulation_result_'+simulation.project_name+'_'+simulation.created_at.strftime("%m/%d/%Y")+'"'

    # Remove zip file after download
    os.remove(zip_path)

    return response

def downloadData(request, id):
    simulation = get_object_or_404(Simulation, id=id)
    input_files = os.getcwd()+ "/media/"+simulation.getInputFolder()+"/"
    zip_path = SheetOutputGenerator.createZip(input_files, "datas")
    
    # Zip all output file and serves to download
    zip_file = open(zip_path, 'rb')
    response = HttpResponse(zip_file, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="simulation_result_{'+str(simulation.id)+'}"'

    # Remove zip file after download
    os.remove(zip_path)

    return response

# Add Questions/Constants page
def index_co(request, type):
    model = MODEL_INPUT_FILES if type == 'input' else MODEL_OUTPUT_FILES

    return render(request, 'co/index.html', {
        "models": os.listdir(model),
        "type": type
    })

@login_required(login_url="simulator:login")
def new_co(request, type):
    model = MODEL_INPUT_FILES if type == 'input' else MODEL_OUTPUT_FILES
    if request.method == "POST":
        # Save file uploaded
        files = request.FILES.getlist('files')
        for f in files:
            default_storage.save(model+str(f), ContentFile(f.read()))
        
        messages.success(request, "The new operations/constants has been register !")
        return redirect("simulator:index_co", type=type)
        
    return render(request, 'co/new.html')

def download_co(request, type, name):
    model = MODEL_INPUT_FILES if type == 'input' else MODEL_OUTPUT_FILES

    path = model+name
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(path)
            return response
    raise Http404
   
def delete_co(request, type, name):
    model = MODEL_INPUT_FILES if type == 'input' else MODEL_OUTPUT_FILES

    path = model+name
    if os.path.exists(path):
        os.remove(path)
        return redirect('simulator:index_co', type=type)
    raise Http404
   
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