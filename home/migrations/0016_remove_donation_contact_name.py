# Generated by Django 5.0.2 on 2024-04-10 15:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0015_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='donation',
            name='contact_name',
        ),
    ]