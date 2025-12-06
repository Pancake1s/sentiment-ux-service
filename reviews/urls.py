from django.urls import path
from .views import upload_step1, upload_step2_import, home, reviews_list

urlpatterns = [
    path("", home, name="home"),
    path("reviews/", reviews_list, name="reviews_list"),
    path("upload/", upload_step1, name="upload_step1"),
    path("upload/import/", upload_step2_import, name="upload_step2_import")
]
