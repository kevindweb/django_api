# Generated by Django 2.0.7 on 2018-08-02 12:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dog_info', '0006_shelters'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Shelters',
            new_name='Shelter',
        ),
    ]
