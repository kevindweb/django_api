# Generated by Django 2.0.7 on 2018-07-29 23:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dog_info', '0004_requestdata_earliest_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dog',
            name='sex',
            field=models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('X', 'Not Given')], max_length=1),
        ),
        migrations.AlterField(
            model_name='requestdata',
            name='earliest_request',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='requestdata',
            name='last_request',
            field=models.DateTimeField(null=True),
        ),
    ]