# celery.py
import os
from celery import Celery

# Définir la variable d'environnement DJANGO_SETTINGS_MODULE pour que Celery puisse trouver votre configuration Django.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azasimul.settings')

app = Celery('azasimul')

# Utiliser la configuration de la base de données à partir de settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches potentielles dans toutes les applications Django inscrites
app.autodiscover_tasks()
