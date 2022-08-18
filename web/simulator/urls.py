from django.urls import path, include
from . import views
from rest_framework import routers

app_name = "simulator"

router = routers.SimpleRouter()
router.register(r'base_element', views.BaseElementView)
router.register(r'base_element_value', views.BaseElementValueView)
router.register(r'possible_specification', views.PossibleSpecificationView)
router.register(r'specification', views.SpecificationView)
router.register(r'composition', views.CompositionView)

urlpatterns = [
    path('', views.index, name='index'),
    path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name= "logout"),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path("form/simulation", views.form_simulation, name="form_simulation"),
    path("form/elements", views.form_elements, name="form_elements"),
    path("api/", include(router.urls))
]
