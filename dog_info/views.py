from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from dog_info.models import Dog
User = get_user_model()
from dog_info.resources.router import RequestResource, Handler
            
class DogView(RequestResource):
    def get(self, request, model, id):
        # receive dog from id
        abstract_request = Handler(
            request, 404, authenticate=True, id=id, model=model)
        return abstract_request.start(Handler.get_logic)
    
    def post(self, request, model):
        # create dog from request data
        data = {
            "error": "Bad request",
            "request_schema": {
                "name": "Rocky (string)",
                "breed": "Golden Retriever (string)",
                "favorite_activity": "Running for frisbees (string)",
                "sex": "M/F/X (character)",
                "birth_day": "06/09/1956 (mm/dd/yyyy)"
            }
        }
        abstract_request = Handler(
            request, 400, default_data=data, authenticate=True, model=Dog)
        return abstract_request.start(Handler.post_logic)
    

@csrf_exempt
@require_POST
def create_user(request):
    # create user with post data
    data = {
        "error": "Bad request",
        "request_schema": {
            "username": "userName (string)",
            "password": "passw0rd1 (string)",
            "email": "example@example.com (email)",
            "full_name": "Patrick Star (string or empty string)"
        }
    }
    abstract_request = Handler(request, 400, default_data=data, model=User)
    return abstract_request.start(Handler.create_user_logic)
