from django.urls import path
from .views import home, reviews_list

urlpatterns = [
    path("", home, name="home"),
    path("reviews/", reviews_list, name="reviews_list"),
]
