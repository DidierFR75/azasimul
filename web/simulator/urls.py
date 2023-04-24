from django.urls import path
from . import views, views_users

app_name = "simulator"

urlpatterns = [
    path('', views.index, name="index"),
    path('new', views.new, name='new'),
    path('edit/<int:id>', views.edit, name='edit'),
    path("delete/<int:id>", views.delete, name="delete"),
    path("compute/<int:simul_id>", views.doCompute, name="compute"),
    path("download/<int:simul_id>", views.downloadData, name="downloadData"),
    path("listdownload/<int:id>", views.listDownloadData, name="listDownloadData"),
    path("downloadonedata/<int:id>/<str:namefile>", views.downloadOneData, name="downloadOneData"),
    # Constants/Operations pages
    path('index_co/<str:type>', views.index_co, name='index_co'),
    path('new_co/<str:type>', views.new_co, name='new_co'),
    path('download_co/<str:type>/<str:name>', views.download_co, name='download_co'),
    path('delete_co/<str:type>/<str:name>', views.delete_co, name='delete_co'),
    # User pages
    path("register", views_users.register_request, name="register"),
    path("login", views_users.login_request, name="login"),
    path("logout", views_users.logout_request, name= "logout"),
    path("password_reset", views_users.password_reset_request, name="password_reset"),
]
