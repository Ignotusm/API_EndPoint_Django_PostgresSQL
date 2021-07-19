from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connection
import json
# Create your views here.


def func():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT date_trunc('second', current_timestamp - pg_postmaster_start_time()) as uptime")

        r = cursor.fetchall()

        return r


def index(request):

    r = func()
    k = ",".join(str(a) for a in r[0])
    print(type(k))
    print(k)

    data = {
        "pgsql": {
            "uptime": k.replace(",", "")
        }
    }

    print(type(data))
    return JsonResponse(data)
