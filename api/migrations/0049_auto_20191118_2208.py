# Generated by Django 2.2.4 on 2019-11-18 22:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0048_auto_20191108_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payrollperiodpayment',
            name='clockin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.Clockin'),
        ),
    ]
