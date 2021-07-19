from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.


def frontpage(request):
    return HttpResponse("<h1>Welcome!</h1>"
                        "<br>DBS-Project-xvlkolensky")
