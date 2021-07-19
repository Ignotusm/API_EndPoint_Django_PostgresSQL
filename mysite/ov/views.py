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


def func_without_return(queryString):
    with connection.cursor() as cursor:
        cursor.execute(queryString)
        connection.commit()


@csrf_exempt
def delete_id(request, id):

    if request.method == 'DELETE':
        delete_rows(id)

    return HttpResponse("Submissions")


# Create your views here.
@csrf_exempt
def index(request):

    if request.method == 'POST':
        received_json_data = json.loads(request.body)

        return createINSERT(received_json_data)

    if request.method == 'GET':

        json_data = createQuery(request.GET)

        return HttpResponse(json_data)

    return HttpResponse("Submissions")


def metadata(GET, query, date):

    page = GET.get('page')
    if(page == None or page.isnumeric() == False):
        page = 1

    per_page = GET.get('per_page')
    if(per_page == None or per_page.isnumeric() == False):
        per_page = 10

    total = func("SELECT COUNT(id) FROM ov.or_podanie_issues"+query+date)
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


def delete_rows(id):

    query = "SELECT bulletin_issue_id,raw_issue_id FROM ov.or_podanie_issues WHERE id={}".format(
        id)

    ids = func(query)
    ids = str(ids[0])
    ids = ids.strip("(").strip(")")
    arr_id = ids.split(", ")

    bull_id = arr_id[0]
    raw_id = arr_id[1]

    query = "DELETE FROM ov.bulletin_issues WHERE id={}".format(bull_id)
    func_without_return(query)
    query = "DELETE FROM ov.raw_issues WHERE id={}".format(raw_id)
    func_without_return(query)
    query = "DELETE FROM ov.or_podanie_issues WHERE id={}".format(id)
    func_without_return(query)


def createINSERT(json_data):

    # BULLETIN ISSUES INSERT
    today = datetime.now()
    bull_year = today.year
    bull_number = func(
        "SELECT MAX(number)  FROM ov.bulletin_issues WHERE  year = '{}'".format(bull_year))
    bull_intNum = str(bull_number[0])
    bull_intNum = bull_intNum.strip("(").strip(")").strip(",")
    bull_number = int(bull_intNum)+1
    bull_published_at = today.strftime("%Y-%m-%d %H:%M:%S")
    bull_created_at = today
    bull_updated_at = today

    queary_insert_bulletin = "INSERT INTO ov.bulletin_issues(year,number,published_at,created_at,updated_at) VALUES ('{}','{}','{}','{}','{}') RETURNING id;".format(
        bull_year, bull_number, bull_published_at, bull_created_at, bull_updated_at)

    bull_id = func(queary_insert_bulletin)
    connection.commit()
    bull_id = str(bull_id[0])
    bull_id = bull_id.strip("(").strip(")").strip(",")
    bull_id = int(bull_id)

    # RAW ISSUES INSERT
    raw_bulletin_issue_id = bull_id
    raw_file_name = "-"
    raw_content = "-"
    raw_created_at = today
    raw_updated_at = today

    queary_insert_raw = "INSERT INTO ov.raw_issues(bulletin_issue_id,file_name,content,created_at,updated_at) VALUES ('{}','{}','{}','{}','{}') RETURNING id;".format(
        raw_bulletin_issue_id, raw_file_name, raw_content, raw_created_at, raw_updated_at)

    raw_id = func(queary_insert_raw)
    connection.commit()
    raw_id = str(raw_id[0])
    raw_id = raw_id.strip("(").strip(")").strip(",")
    raw_id = int(raw_id)

    # OR_POADANIE_ISSUES_INSERT
    orpi_bull_id = bull_id
    orpi_raw_id = raw_id
    orpi_br_mark = "-"
    orpi_br_court_code = "-"
    orpi_br_court_name = json_data["response"]["br_court_name"]
    orpi_kind_code = "-"
    orpi_kind_name = json_data["response"]["kind_name"]
    orpi_cin = json_data["response"]["cin"]
    orpi_registration_date = today
    orpi_corporate_body_name = json_data["response"]["corporate_body_name"]
    orpi_br_section = json_data["response"]["br_section"]
    orpi_br_insertion = "-"
    orpi_text = json_data["response"]["text"]
    orpi_created_at = today
    orpi_updated_at = today
    orpi_address_line = "{}, {} {}".format(
        json_data["response"]["street"], json_data["response"]["postal_code"], json_data["response"]["city"])
    orpi_street = json_data["response"]["street"]
    orpi_postal_code = json_data["response"]["postal_code"]
    orpi_city = json_data["response"]["city"]

    queary_insert_or_podanie_issues = "INSERT INTO ov.or_podanie_issues(bulletin_issue_id,raw_issue_id,br_mark,br_court_code,br_court_name,kind_code,kind_name,cin,registration_date,corporate_body_name,br_section,br_insertion,text,created_at,updated_at,address_line,street,postal_code,city) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}') RETURNING id".format(
        orpi_bull_id, orpi_raw_id, orpi_br_mark, orpi_br_court_code, orpi_br_court_name, orpi_kind_code, orpi_kind_name, orpi_cin, orpi_registration_date, orpi_corporate_body_name, orpi_br_section, orpi_br_insertion, orpi_text, orpi_created_at, orpi_updated_at, orpi_address_line, orpi_street, orpi_postal_code, orpi_city)

    final_queary = func(queary_insert_or_podanie_issues)
    connection.commit()

    return HttpResponse("Good")


def createJSON(data):

    newData = []

    for row in data:

        datum = row[9]

        if(datum != None):
            datum = row[9].strftime("%Y/%m/%d")

        new_dict = {
            "id": row[0],
            "br_court_name": row[4],
            "kind_name": row[6],
            "cin": row[8],
            "registration_date": datum,
            "corporate_body_name": row[10],
            "br_section": row[11],
            "text": row[13],
            "street": row[17],
            "postal_code": row[18],
            "city": row[19]
        }

        newData.append(new_dict)

    return newData


def func(queryString):
    with connection.cursor() as cursor:
        cursor.execute(queryString)
        r = cursor.fetchall()

        return r


def createQuery(GET):

    queryString = "SELECT * FROM ov.or_podanie_issues"

    # QUERY
    query = ""

    quearyparam = GET.get('query')

    if(GET.get('query') != None):
        if(quearyparam.isnumeric()):
            query = " WHERE cin LIKE '%{}%'".format(quearyparam)
        else:
            quearyparam = quearyparam.replace("%20", " ")
            query = " WHERE (corporate_body_name LIKE '%{}%' OR city LIKE '%{}%')".format(
                quearyparam, quearyparam)

    # DATE
    dateGTE = GET.get('registration_date_gte')
    dateLTE = GET.get('registration_date_lte')

    queryDate = ""

    if(dateGTE != None):
        dateGTE = parse(dateGTE)
        if(query != ""):
            queryDate = queryDate + \
                " AND registration_date >= '{}'".format(dateGTE)
        else:
            queryDate = queryDate + \
                " WHERE registration_date >= '{}'".format(dateGTE)
    if(dateLTE != None):
        dateLTE = parse(dateLTE)
        if(query != "" and dateGTE != None):
            queryDate = queryDate + \
                " AND registration_date <= '{}'".format(dateLTE)
        else:
            queryDate = queryDate + \
                " WHERE registration_date <= '{}'".format(dateLTE)

    # ORDER
    orderBy = GET.get('order_by')
    orderType = GET.get('order_type')

    queryOrder = ""

    if(orderBy != None and orderType != None):
        queryOrder = " ORDER BY {} {}".format(orderBy, orderType)
    else:
        queryOrder = " ORDER BY id DESC"

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
