# Generated by Django 2.0 on 2018-09-10 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_auto_20180904_2046'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='status',
            field=models.CharField(blank=True, choices=[('ACTIVE', 'Active'), ('PAUSED', 'Paused'), ('SUSPENDED', 'Suspended')], default='ACTIVE', max_length=9),
        ),
    ]