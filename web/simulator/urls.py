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
    # Base Elements pages
    path('base_elements', views.index_base_element, name="index_base_element"),
    path("new_base_element", views.new_base_element, name="new_base_element"),
    path('detail_base_element/<int:id>', views.detail_base_element, name='detail_base_element'),
    path('edit_base_element/<int:id>', views.edit_base_element, name='edit_base_element'),
    path("delete_base_element/<int:id>", views.delete_base_element, name="delete_base_element"),
    # User pages
    path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name= "logout"),
    path("password_reset", views.password_reset_request, name="password_reset"),
]
