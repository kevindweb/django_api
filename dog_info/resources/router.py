import logging
from dog_info.resources.handler import Handler
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
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
    model_data = {
        "dog": {
            "error": "Bad request",
            "request_schema": {
                "name": "Rocky (string)",
                "breed": "Golden Retriever (string)",
                "favorite_activity": "Running for frisbees (string)",
                "sex": "M/F/X (character)",
                "birth_day": "06/09/1956 (mm/dd/yyyy)"
            }
        },
        "shelter": {
            "error": "Bad request",
            "request_schema": {
                "name": "My Animal Shelter (string)",
                "number_dogs": "120 (integer)",
                "manager_name": "Manager Supremo (string)"
            }
        }
    }
    http_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    http_methods_with_body = ['POST', 'PUT', 'PATCH']
    # accepted methods
    logs = logging.getLogger(__name__)

    def get(self, request, model, id):
        # receive dog from id
        abstract_request = Handler(
            request, 404, model, authenticate=True, id=id)
        return abstract_request.start(Handler.get)

    def post(self, request, model, data):
        # create dog from request data
        abstract_request = Handler(
            request, 400, model, default_data=data, authenticate=True)
        return abstract_request.start(Handler.post)

    def delete(self, request, model, id):
        # delete dog with id
        abstract_request = Handler(
            request, 404, model, authenticate=True, id=id)
        return abstract_request.start(Handler.delete)

    @classmethod
    @csrf_exempt
    def dispatch(cls, request, *args, **kwargs):
        # try:
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
                    if request.method in cls.http_methods_with_body:
                        print(item_path)
                        kwargs["data"] = cls.model_data[item_path.lower()]
                    # custom schema for this object model
                    return handler_method(request, model, **kwargs)

            methods = [method for method in cls.http_methods if get_handler_method(
                request_handler, method)]
            if len(methods) > 0:
                raise Exception("HTTP method not allowed", 405)
            else:
                raise Exception("Page not found", 404)
        # except Exception as e:
        #     # handle any exception by returning it and the status code
        #     print(type(e).__name__)
        #     if e == None or len(e.args) == 0:
        #         msg = "Unknown error"
        #         status = 500
        #     else:
        #         msg = e.args[0]
        #         if len(e.args) > 1:
        #             status = e.args[1]
        #         else:
        #             # we don't know the status code
        #             status = 500
        #     error = {
        #         "error": msg
        #     }
        #     if status == 500:
        #         cls.logs.error(msg)
        #     else:
        #         cls.logs.debug(msg)
        #     # log the error
        #     return JsonResponse(error, status=status, json_dumps_params={"indent": 2})
