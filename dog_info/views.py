import json
import logging
from datetime import datetime, timezone
from django.http import JsonResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth import get_user_model
from dog_info.models import Dog, RequestData
User = get_user_model()


class Handler():
    request_limit = 20
    curr_timezone = timezone.utc
    app_name = "dog_info"
    def __init__(self, request, default_status, **kwargs):
        self.request = request
        self.status = default_status
        self.id = kwargs.get("id", "")
        self.data = kwargs.get("default_data", {})
        self.authenticate = kwargs.get("authenticate", False)
        self.model = kwargs.get("model", None)
        if not self.model:
            raise Exception("No abstracted model", 500)
        self.logs = logging.getLogger(__name__)

    def get_client_ip(self):
        try:
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            return ip
        except:
            # we could not get ip address
            raise Exception("Error validating ip address", 500)

    def check_request_num(self):
        self.ip_address = self.get_client_ip()
        timeout = False
        num_requests = 0
        try:
            request_data = RequestData.objects.filter(ip_address=self.ip_address)
        except:
            raise Exception("Error finding ip address", 500)
        if len(request_data) > 0:
            # ip is defined
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
        else:
            # ip address has not been set
            timeout = True
        return timeout, num_requests

    def authenticate_request(self):
        try:
            api_token = self.request.META.get('HTTP_TOKEN')
        except:
            raise Exception("'Token' header not found", 401)
        try:
            authenticated = len(User.objects.filter(
                api_token=api_token)) > 0
        except:
            raise Exception("Invalid token", 401)
        if not authenticated:
            raise Exception("Authentication failed", 401)
        # otherwise continue

    def start(self, func):
        # receive request and apply context-given logic
        try:
            request_timeout, num_requests = self.check_request_num()
            if request_timeout:
                if num_requests > 0:
                    raise Exception(
                        "You have made %s requests this hour" % num_requests, 429)
                    # we've recieved too many requests from this IP 
                elif func.__name__ != "create_user_logic":
                    # a user has not been created on this ip
                    raise Exception("A user has not been created yet", 401)
            if self.authenticate:
                # need to authenticate api_token before moving forward
                self.authenticate_request()
            if self.request.method == "GET":
                func(self, self.model, self.id)
            else:
                body = json.loads(self.request.body)
                if set(body.keys()) == set(self.data["request_schema"].keys()):
                    func(self, self.model, body)
                    # call the function passed in to handle specific logic
            if self.item['model'] == ("%s.user" % self.app_name):
                # remove fields unnecessary for API user
                del self.item['pk']
                del self.item["fields"]["last_login"]
                del self.item["fields"]["is_staff"]
                del self.item["fields"]["is_superuser"]
                del self.item["fields"]["groups"]
                del self.item["fields"]["user_permissions"]
            del self.item['model']
            # remove model property
            self.data = {"data": self.item}
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
            return JsonResponse(error, status=status, json_dumps_params={"indent": 2})

    def get_logic(self, model, id):
        # our objects have the same keys
            self.status = 200
            try:
                items = model.objects.filter(id=id)
            except:
                raise Exception("Error finding item", 500)
            if len(items) == 0:
                raise Exception("Could not find item", 404)
            self.item = json.loads(serializers.serialize('json', [items[0], ]))[0]
                
    
    def create_user_logic(self, model, body):
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
                # try:
                ip = RequestData.objects.filter(ip_address=self.ip_address)
                if len(ip) > 0:
                    ip = ip[0]
                    if not user in ip.users.all():
                        # check for duplicate
                        ip.users.add(user)
                        # add user to current ip address
                else:
                    # add ip address
                    now = datetime.now(self.curr_timezone)
                    ip = RequestData.objects.create(
                        ip_address=self.ip_address, earliest_request=now, last_request=now, requests_this_hour=1)
                    ip.users.add(user)
                # except:
                #     raise Exception("User couldn't be added to ip address", 500)
        elif not user.check_password(password):
            raise Exception("User already created but invalid password", 401)
        else:
            self.status = 200
            # already created this valid user
        self.item = json.loads(serializers.serialize('json', [user, ]))[0]
            

@csrf_exempt
@require_GET
def get_dog(request, id):
    # receive dog from id 
    print(request.method)
    abstract_request = Handler(request, 400, authenticate=True, id=id, model=Dog)
    return abstract_request.start(Handler.get_logic)

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
    abstract_request = Handler(request, 400, default_data=data, model=User)
    return abstract_request.start(Handler.create_user_logic)
