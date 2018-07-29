from django.http import JsonResponse
import logging

logs = logging.getLogger(__name__)

class ErrorHandler():
    def __init__(self, status, request, msg="Unknown error"):
        self.status = status
        self.request = request
        self.msg = msg
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def handle(self):
        if self.msg == "Unknown error":
            log_msg = ("Status: %s -- Exception: %s -- Ip: %s" %
                       (self.status, self.msg, self.get_client_ip()))
            logs.error(log_msg)
        else:
            log_msg = ("Status: %s -- Path: %s -- Ip: %s" %
                       (self.status, self.msg, self.get_client_ip()))
            logs.warning(log_msg)
            self.msg = "URL is invalid"
        err = {
            "error": self.msg
        }
        return JsonResponse(err, status=self.status, json_dumps_params={"indent": 2})


def handler404(request, **kwargs):
    ex = kwargs.get("exception")
    msg = ex.args[0] if ex.args and len(ex.args) > 0 else "Uknown error"
    return ErrorHandler(404, request, msg['path']).handle()

def handler500(request):
    msg = "Server error handling request"
    return ErrorHandler(500, request, msg).handle()
