from django.contrib import admin
from django.urls import path, include

from dog_info import views

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path('api/v1/get_dog/<uuid:id>', views.get_dog),
    path('api/v1/create_user', views.create_user)
]

handler404 = "dog_info.errors.handler404"
handler500 = "dog_info.errors.handler500"