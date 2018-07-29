# Generated by Django 2.0.7 on 2018-07-28 23:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dog_info', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(unique=True)),
                ('last_request', models.DateField()),
                ('requests_this_hour', models.IntegerField()),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
