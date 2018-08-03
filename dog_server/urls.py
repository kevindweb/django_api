from django.contrib import admin
from django.urls import path, include

from dog_info import views
from dog_info.resources import router

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path('api/v1/dog/<uuid:id>', router.RequestResource.dispatch),
    path('api/v1/dog', router.RequestResource.dispatch),
    path('api/v1/shelter/<uuid:id>', router.RequestResource.dispatch),
    path('api/v1/shelter', router.RequestResource.dispatch),
    # for post request we don't need id
    path('api/v1/create_user', views.create_user),
]

handler404 = "dog_info.errors.handler404"
handler500 = "dog_info.errors.handler500"
