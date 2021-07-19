from django.urls import path
from . import views

urlpatterns = [
    path('companies/', views.index, name='index'),
]
