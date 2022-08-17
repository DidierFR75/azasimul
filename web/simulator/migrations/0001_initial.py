# Generated by Django 3.2.15 on 2022-08-16 17:35

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255)),
                ('value', models.FloatField()),
                ('unit', models.JSONField()),
                ('unit_separator', models.CharField(choices=[(None, 'Null'), ('/', 'By')], default=None, max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='Composition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_elements', models.ManyToManyField(to='simulator.BaseElement')),
            ],
        ),
        migrations.CreateModel(
            name='PossibleSpecification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specification_name', models.CharField(max_length=255)),
                ('functions_associate', models.JSONField()),
                ('functions_parameters', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='Simulation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField()),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Specification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('composition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulator.composition')),
                ('specifications_possible', models.ManyToManyField(to='simulator.PossibleSpecification')),
            ],
        ),
        migrations.CreateModel(
            name='BaseElementValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_element', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simulator.baseelement')),
            ],
        ),
    ]