import json
import logging
from datetime import datetime, timezone
from django.http import JsonResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from dog_info.models import Dog, RequestData
User = get_user_model()


class Handler():
    request_limit = 10
    curr_timezone = timezone.utc
    def __init__(self, request, default_data, default_status):
        self.request = request
        self.data = default_data
        self.status = default_status
        self.logs = logging.getLogger(__name__)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def check_request_num(self):
        ip_address = self.get_client_ip()
        timeout = False
        num_requests = 0
        try:
            request_data = RequestData.objects.filter(ip_address=ip_address)
        except:
            raise Exception("Error finding ip address", 500)
        if len(request_data) > 0:
            # not first request
            request_data = request_data[0]
            request_data.last_request = datetime.now(self.curr_timezone)
            earliest_request = request_data.earliest_request
            update_fields = ["requests_this_hour", "last_request"]
            if (request_data.last_request - earliest_request).total_seconds() > 3600:
                # the hour is done, reset the request count
                request_data.earliest_request = datetime.now(self.curr_timezone)
                request_data.requests_this_hour = 1
                update_fields += ["earliest_request"]
                # update earliest request as well 
            else:
                request_data.requests_this_hour += 1
            request_data.save(update_fields=update_fields)
            num_requests = request_data.requests_this_hour
            if num_requests > self.request_limit:
                timeout = True
        return timeout, num_requests

    def start(self, func):
        # receive request and apply context-given logic
        try:
            request_timeout, num_requests = self.check_request_num()
            if request_timeout:
                raise Exception(
                    "You have made %s requests this hour" % num_requests, 429)
                # we've recieved too many requests from this IP 
            body = json.loads(self.request.body)
            if set(body.keys()) == set(self.data["request_schema"].keys()):
                func(self, body)
                # call the function passed in to handle specific logic
            return JsonResponse(self.data, status=self.status)
        except Exception as e:
            # handle any exception by returning it and the status code
            if e == None or len(e.args) == 0:
                msg = "Unknown error"
                status = 500
            else:
                msg = e.args[0]
                if len(e.args) > 1:
                    status = e.args[1]
                else:
                    # we don't know the status code
                    status = 500
            error = {
                "error": msg
            }
            self.logs.debug(msg)
            return JsonResponse(error, status=status)

    def get_dog_logic(self, body):
        # our objects have the same keys
            self.status = 200
            try:
                authenticated = len(User.objects.filter(
                    api_token=body["api_token"])) > 0
            except:
                raise Exception("Invalid api_token", 401)
            if authenticated:
                try:
                    dog = Dog.objects.filter(id=body["dog"])
                except:
                    raise Exception("Error finding dog", 500)
                if len(dog) == 0:
                    raise Exception("Could not find dog", 404)
                dog = serializers.serialize('json', [dog[0], ])
                self.data = {"dog": dog}
            else:
                raise Exception("Authentication failed", 401)
    
    def create_user_logic(self, body):
        username = body['username']
        password = body['password']
        email = body['email']
        full_name = body['full_name']
        # user = User.objects.filter(username=username).first()
        user = User.objects.filter(username=username)
        if len(user) > 0:
            user = user[0]
        if not user:
            # username with those credentials does not exist
            if(len(User.objects.filter(email=email)) > 0):
                # user with the same email already exists
                raise Exception("User with that email already exists", 400)
            else:
                try:
                    first_name = ""
                    last_name = ""
                    if full_name != "":
                        # parse the name into first and last
                        split_name = full_name.split(" ")
                        first_name = split_name[0]
                        if len(split_name) > 1:
                            last_name = split_name[1]
                    user = User.objects.create_user(
                        username=username, email=email, password=password, first_name=first_name, last_name=last_name)
                except:
                    raise Exception("Could not create user", 500)
                user.save()
                self.status = 201
        elif not user.check_password(password):
            raise Exception("User already created but invalid password", 401)
        else:
            self.status = 200
            # already created this valid user
        user = serializers.serialize('json', [user, ])
        self.data = {
            "user": user
        }
            

@csrf_exempt
@require_POST
def get_dog(request):
    # receive dog from id 
    data = {
        "error": "Bad request",
        "request_schema": {
            "api_token": "UUID",
            "dog": "UUID"
        }
    }
    abstract_request = Handler(request, data, 400)
    return abstract_request.start(Handler.get_dog_logic)

@csrf_exempt
@require_POST
def create_user(request):
    # create user with post data
    data = {
        "error": "Bad request",
        "request_schema": {
            "username": "string",
            "password": "string",
            "email": "string as email",
            "full_name": "string (can be empty)"
        }
    }
    abstract_request = Handler(request, data, 400)
    return abstract_request.start(Handler.create_user_logic)
