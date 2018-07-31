import json
import logging
import re
from datetime import datetime, timezone
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core import serializers
from dog_info.models import RequestData
import dog_info.models as AllModels
from django.contrib.auth import get_user_model
User = get_user_model()

def get_handler_method(request_handler, http_method):
    try:
        handler_method = getattr(request_handler, http_method.lower())
        # check to see if we defined the logic for this HTTP method
        if callable(handler_method):
            return handler_method
    except AttributeError:
        pass


class RequestResource:
    http_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    # accepted methods
    logs = logging.getLogger(__name__)

    @classmethod
    @csrf_exempt
    def dispatch(cls, request, *args, **kwargs):
        try:
            item_path = request.path.split("/")[3].capitalize()
            # get django model from path
            if hasattr(AllModels, item_path):
                model = getattr(AllModels, item_path)
            else:
                raise Exception("Model not found", 500)
            request_handler = cls()
            # cls / self
            if request.method in cls.http_methods:
                handler_method = get_handler_method(
                    request_handler, request.method)
                if handler_method:
                    return handler_method(request, model, *args, **kwargs)

            methods = [method for method in cls.http_methods if get_handler_method(
                request_handler, method)]
            if len(methods) > 0:
                raise Exception("HTTP method not allowed", 405)
            else:
                raise Exception("Page not found", 404)
        except Exception as e:
            # handle any exception by returning it and the status code
            print(type(e).__name__)
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
            if status == 500:
                cls.logs.error(msg)
            else:
                cls.logs.debug(msg)
            # log the error
            return JsonResponse(error, status=status, json_dumps_params={"indent": 2})


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
        self.warnings = []
        if "request_schema" in self.data:
            self.fields = list(self.data["request_schema"].keys())
        if not self.model:
            raise Exception("No item model", 500)

    def error(self, msg, code):
        # avoid exceptions as much as possible
        if hasattr(self, "item"):
            del self.item
            # make sure there are no errors with
        self.status = code
        self.error_msg = {
            "error msgs": msg
        }
        return JsonResponse(self.error_msg, status=self.status)

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
            request_data = RequestData.objects.filter(
                ip_address=self.ip_address)
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
                request_data.earliest_request = datetime.now(
                    self.curr_timezone)
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

    def char_check(self, x):
        return str(x)[0]

    def str_check(self, x):
        return str(x)

    def int_check(self, x):
        return int(x)

    def datetime_check(self, x):
        return datetime.strptime(x, "%m/%d/%Y")

    def assert_fields(self, body):
        # type check each field
        field_to_type = {
            "string": self.str_check,
            "string or empty string": self.str_check,
            "email": self.str_check,
            "integer": self.int_check,
            "mm/dd/yyyy": self.datetime_check, 
            "character": self.char_check
        }
        for field in self.fields:
            field_value = self.data["request_schema"][field]
            field_type = re.search(r'\((.*?)\)', field_value).group(1)
            try:
                body[field] = field_to_type[field_type](body[field])
            except:
                self.err_pass
        return body

    def start(self, func):
        # receive request and apply context-given logic
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
            response = func(self, self.model, self.id)
            if response:
                return response
                # we errored out
        else:
            body = json.loads(self.request.body)
            if set(body.keys()) == set(self.fields):                
                # parse the specific type of field (datetime for example)
                self.err_pass = False
                try:
                    body = self.assert_fields(body)
                except:
                    self.err_pass = True
                if not self.err_pass:
                    # call the function passed in to handle specific logic
                    response = func(self, model=self.model, body=body, id=self.id)
                    if response:
                        return response
        if hasattr(self, "item"):
            # item will only be here if query was successful
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
        self.data = {"data": self.item if hasattr(self, "item") else self.data}
        if len(self.warnings) > 0:
            # give user response some warnings
            self.data["warnings"] = self.warnings
        return JsonResponse(self.data, status=self.status)

    def get_logic(self, model, id):
        # our objects have the same keys
        try:
            items = model.objects.filter(id=id)
        except:
            return self.error("Error finding item", 500)
        if len(items) == 0:
            return self.error("Could not find item", 404)
        self.status = 200
        self.item = json.loads(
            serializers.serialize('json', [items[0], ]))[0]

    def post_logic(self, **kwargs):
        # logic to run if we get a post request with required data
        model = kwargs.get("model")
        body = kwargs.get("body")
        try:
            item = model.objects.create(**body)
        except IntegrityError:
            return self.error("Invalid request field format", 400)
        except:
            return self.error("Could not create item", 500)
        self.status = 201
        self.item = json.loads(serializers.serialize('json', [item, ]))[0]

    def create_user_logic(self, **kwargs):
        body = kwargs.get("body")
        username = body['username']
        password = body['password']
        email = body['email']
        full_name = body['full_name']
        user = User.objects.filter(username=username)
        if len(user) > 0:
            user = user[0]
        if not user:
            # username with those credentials does not exist
            if(len(User.objects.filter(email=email)) > 0):
                # user with the same email already exists
                return self.error("User with that email already exists", 400)
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
                    return self.error("Could not create user", 500)
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
        elif not user.check_password(password):
            return self.error("User already created but invalid password", 401)
        else:
            self.status = 200
            # already created this valid user
        self.item = json.loads(serializers.serialize('json', [user, ]))[0]
