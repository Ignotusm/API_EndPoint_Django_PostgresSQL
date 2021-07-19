from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connection
from datetime import datetime
from dateutil.parser import parse
import math
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
import json

# Create your views here.


@csrf_exempt
def index(request):

    if request.method == 'GET':

        json_data = createQuery(request.GET)

        return HttpResponse(json_data)

    return HttpResponse("<h1>Welcome companies</h1>"
                        "<br>DBS-Project-xvlkolensky")


def func(queryString):
    with connection.cursor() as cursor:
        cursor.execute(queryString)
        r = cursor.fetchall()

        return r


def createJSON(data):

    newData = []

    for row in data:

        datum = row[4]

        if(datum != None):
            datum = row[4].strftime("%Y/%m/%d")

        new_dict = {
            "cin": row[0],
            "name": row[1],
            "br_section": row[2],
            "address_line": row[3],
            "last_update": datum,
            "or_podanie_issues_count": row[5],
            "znizenie_imania_issues_count": row[6],
            "likvidator_issues_count": row[7],
            "konkurz_vyrovnanie_issues_count": row[8],
            "konkurz_restrukturalizacia_actors_count": row[9],
        }

        newData.append(new_dict)

    return newData


def metadata(GET, query, date):

    page = GET.get('page')
    if(page == None or page.isnumeric() == False):
        page = 1

    per_page = GET.get('per_page')
    if(per_page == None or per_page.isnumeric() == False):
        per_page = 10

    total = func("SELECT COUNT(cin) FROM (SELECT c.cin,c.name,c.br_section,c.address_line,c.last_update, table1.or_podanie_issues_count,table2.znizenie_imania_issues_count,table3.likvidator_issues_count, table4.konkurz_vyrovnanie_issues_count,table5.konkurz_restrukturalizacia_actors_count FROM ov.companies c left join (select cin, count(*) or_podanie_issues_count from ov.or_podanie_issues group by cin) table1 on table1.cin = c.cin left join (select cin, count(*) znizenie_imania_issues_count from ov.znizenie_imania_issues group by cin) table2 on table2.cin = c.cin left join (select cin, count(*) likvidator_issues_count from ov.likvidator_issues group by cin) table3 on table3.cin = c.cin left join (select cin, count(*) konkurz_vyrovnanie_issues_count from ov.konkurz_vyrovnanie_issues group by cin) table4 on table4.cin = c.cin left join (select cin, count(*) konkurz_restrukturalizacia_actors_count from ov.konkurz_restrukturalizacia_actors group by cin) table5 on table5.cin = c.cin) as table1"+query+date)
    total = str(total[0])
    total = total.strip("(").strip(")").strip(",")
    total = int(total)

    pages = math.ceil(int(total)/int(per_page))

    mdata = {
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "total": total
    }

    return mdata


def createQuery(GET):

    queryString = "SELECT * FROM (SELECT c.cin,c.name,c.br_section,c.address_line,c.last_update, table1.or_podanie_issues_count,table2.znizenie_imania_issues_count,table3.likvidator_issues_count, table4.konkurz_vyrovnanie_issues_count,table5.konkurz_restrukturalizacia_actors_count FROM ov.companies c left join (select cin, count(*) or_podanie_issues_count from ov.or_podanie_issues group by cin) table1 on table1.cin = c.cin left join (select cin, count(*) znizenie_imania_issues_count from ov.znizenie_imania_issues group by cin) table2 on table2.cin = c.cin left join (select cin, count(*) likvidator_issues_count from ov.likvidator_issues group by cin) table3 on table3.cin = c.cin left join (select cin, count(*) konkurz_vyrovnanie_issues_count from ov.konkurz_vyrovnanie_issues group by cin) table4 on table4.cin = c.cin left join (select cin, count(*) konkurz_restrukturalizacia_actors_count from ov.konkurz_restrukturalizacia_actors group by cin) table5 on table5.cin = c.cin) as table1"

    # QUERY
    query = ""

    quearyparam = GET.get('query')

    if(GET.get('query') != None):
        if(quearyparam.isnumeric()):
            query = " WHERE cin LIKE '%{}%'".format(quearyparam)
        else:
            quearyparam = quearyparam.replace("%20", " ")
            query = " WHERE (name LIKE '%{}%' OR address_line LIKE '%{}%')".format(
                quearyparam, quearyparam)

    # DATE
    dateGTE = GET.get('last_update_gte')
    dateLTE = GET.get('last_update_lte')

    queryDate = ""

    if(dateGTE != None):
        dateGTE = parse(dateGTE)
        if(query != ""):
            queryDate = queryDate + \
                " AND last_update >= '{}'".format(dateGTE)
        else:
            queryDate = queryDate + \
                " WHERE last_update >= '{}'".format(dateGTE)
    if(dateLTE != None):
        dateLTE = parse(dateLTE)
        if(query != "" and dateGTE != None):
            queryDate = queryDate + \
                " AND last_update <= '{}'".format(dateLTE)
        else:
            queryDate = queryDate + \
                " WHERE last_update <= '{}'".format(dateLTE)

    # ORDER
    orderBy = GET.get('order_by')
    orderType = GET.get('order_type')

    queryOrder = ""

    if(orderBy != None and orderType != None):
        queryOrder = " ORDER BY {} {}".format(orderBy, orderType)

    # PAGING
    page = 1
    per_page = 10
    if(GET.get('page') == None):
        page = 1
    else:
        if(GET.get('page').isnumeric()):
            page = int(GET.get('page'))
        else:
            page = 1

    if(GET.get('per_page') == None):
        per_page = 10
    else:
        if(GET.get('per_page').isnumeric()):
            per_page = int(GET.get('per_page'))
        else:
            per_page = 10

    queryString = queryString + query + queryDate + queryOrder + " LIMIT {} OFFSET {};".format(
        per_page, (page-1)*per_page)

    data = func(queryString)
    mdata = metadata(GET, query, queryDate)

    newData = createJSON(data)

    data = {
        "items": newData,
        "metadata": mdata
    }

    json_data = json.dumps(data)

    return json_data
