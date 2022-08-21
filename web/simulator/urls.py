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
    # Composite pages
    path('composites', views.index_composite, name="index_composite"),
    path("new_composite", views.new_composite, name="new_composite"),
    path('detail_composite/<int:id>', views.detail_composite, name='detail_composite'),
    path('edit_composite/<int:id>', views.edit_composite, name='edit_composite'),
    path("delete_composite/<int:id>", views.delete_composite, name="delete_composite"),
    # User pages
    path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name= "logout"),
    path("password_reset", views.password_reset_request, name="password_reset"),
]
