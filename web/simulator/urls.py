from django.urls import path
from . import views

app_name = "simulator"

urlpatterns = [
    path('', views.index, name="index"),
    path('new', views.new, name='new'),
    path('detail/<int:id>', views.detail, name='detail'),
    path('edit/<int:id>', views.edit, name='edit'),
    path("delete/<int:id>", views.delete, name="delete"),
    path("generate/<int:id>", views.generateCSV, name="csv"),
    # Constants/Operations pages
    path('new_co', views.new_co, name='new_co'),

    # User pages
    path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name= "logout"),
    path("password_reset", views.password_reset_request, name="password_reset"),
]
