from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
User = get_user_model()
from dog_info.resources.router import Handler    

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
