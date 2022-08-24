from lib2to3.pytree import Base
from django.contrib import admin
from .models import Simulation, BaseComposite, BaseElement
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

admin.site.register(Simulation)
admin.site.register(BaseElement)

class MyAdmin(TreeAdmin):
    form = movenodeform_factory(BaseComposite)

admin.site.register(BaseComposite, MyAdmin)