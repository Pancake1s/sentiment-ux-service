from django.shortcuts import render
from .models import Review

def home(request):
    return render(request, "home.html")

def reviews_list(request):
    qs = Review.objects.all()[:50]
    return render(request, "reviews_list.html", {"reviews": qs})
