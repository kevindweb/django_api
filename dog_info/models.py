import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # token will be used for authentication without cookies
    api_token = models.UUIDField(default=uuid.uuid4, unique=True)
        
max_field_length = 50

class Dog(models.Model):
    sex_choices = [('M', 'Male'), ('F', 'Female'), ('X', 'Not Given')]
    # data model below
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=max_field_length)
    birth_day = models.DateField()
    # want to set default birthday as datetime.date(1998, 8, 26)
    breed = models.CharField(max_length=max_field_length, blank=True)
    favorite_activity = models.TextField()
    sex = models.CharField(choices=sex_choices, max_length=1)
    objects = models.Manager()

class Shelter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=max_field_length)
    number_dogs = models.IntegerField()
    manager_name = models.CharField(max_length=max_field_length)
    objects = models.Manager()

class RequestData(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    users = models.ManyToManyField(User)
    earliest_request = models.DateTimeField(null=True)
    last_request = models.DateTimeField(null=True)
    requests_this_hour = models.IntegerField()
    objects = models.Manager()
