# Generated by Django 5.0.2 on 2024-04-02 13:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0013_ngo_delete_ngouser'),
    ]

    operations = [
        migrations.CreateModel(
            name='NGOProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('image1', models.ImageField(upload_to='images/')),
                ('ngo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='home.ngo')),
            ],
        ),
    ]