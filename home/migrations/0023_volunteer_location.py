# Generated by Django 5.0.4 on 2024-04-20 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0022_alter_donation_other_products'),
    ]

    operations = [
        migrations.AddField(
            model_name='volunteer',
            name='location',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
    ]