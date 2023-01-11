from django.urls import path
from . import views

app_name = "simulator"

urlpatterns = [
    path('', views.index, name="index"),
    path('new', views.new, name='new'),
    path('edit/<int:id>', views.edit, name='edit'),
    path("delete/<int:id>", views.delete, name="delete"),
    path("generate/<int:id>", views.generateCSV, name="csv"),
    path("download/<int:id>", views.downloadData, name="downloadData"),
    path("listdownload/<int:id>", views.listDownloadData, name="listDownloadData"),
    path("downloadonedata/<int:id>/<str:namefile>", views.downloadOneData, name="downloadOneData"),
    # Constants/Operations pages
    path('index_co/<str:type>', views.index_co, name='index_co'),
    path('new_co/<str:type>', views.new_co, name='new_co'),
    path('download_co/<str:type>/<str:name>', views.download_co, name='download_co'),
    path('delete_co/<str:type>/<str:name>', views.delete_co, name='delete_co'),
    # User pages
    path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name= "logout"),
    path("password_reset", views.password_reset_request, name="password_reset"),
]
