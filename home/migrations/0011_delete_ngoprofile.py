# Generated by Django 5.0.2 on 2024-04-01 13:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_ngoprofile_delete_ngo'),
    ]

    operations = [
        migrations.DeleteModel(
            name='NGOProfile',
        ),
    ]