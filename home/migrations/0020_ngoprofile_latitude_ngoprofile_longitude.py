# Generated by Django 5.0.2 on 2024-04-12 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_donor'),
    ]

    operations = [
        migrations.AddField(
            model_name='ngoprofile',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ngoprofile',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
