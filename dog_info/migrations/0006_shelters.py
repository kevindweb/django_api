# Generated by Django 2.0.7 on 2018-08-02 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dog_info', '0005_auto_20180729_2357'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shelters',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('number_dogs', models.IntegerField()),
                ('manager_name', models.CharField(max_length=50)),
            ],
        ),
    ]