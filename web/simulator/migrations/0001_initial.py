# Generated by Django 4.1 on 2023-11-30 17:39

import ckeditor.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simulator.models
import simulator.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Simulation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('project_name', models.CharField(blank=True, max_length=255, unique=True)),
                ('project_description', ckeditor.fields.RichTextField(blank=True)),
                ('project_type', models.CharField(blank=True, choices=[('Stand Alone Storage', 'Stand Alone Storage'), ('PV + Storage', 'PV + Storage'), ('Wind + Storage', 'Wind + Storage'), ('Mobility Applications', 'Mobility Applications')], default='Stand Alone Storage', max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SimulationInput',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_file', models.FileField(blank=True, null=True, upload_to=simulator.models.simulation_directory_path, validators=[simulator.validators.validate_file_extension])),
                ('simulation', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='simulation_input', related_query_name='simulation_input', to='simulator.simulation')),
            ],
        ),
    ]
