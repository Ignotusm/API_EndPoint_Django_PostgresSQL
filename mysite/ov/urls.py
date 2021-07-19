from django.urls import path

from . import views

urlpatterns = [
    path('ov/submissions/', views.index, name='index'),
    path('ov/submissions/<id>', views.delete_id, name='delete_id')
]
