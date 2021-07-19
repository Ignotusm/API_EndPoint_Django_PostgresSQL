from django.shortcuts import render
from django.http import HttpResponse
from mysite.models import OrPodanieIssues
from mysite.models import BulletinIssues
from mysite.models import RawIssues
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import math
import json
from dateutil.parser import parse
from datetime import datetime
from django.db.models import Max

# Create your views here.


@csrf_exempt
def index(request):

    if(request.method == 'GET'):
        data = createQuery(request.GET)
        return HttpResponse(data, status=200)

    elif(request.method == 'POST'):
        received_json_data = json.loads(request.body)

        result = createINSERT(received_json_data)
        return result


@csrf_exempt
def delete_id(request, id):

    if(request.method == 'GET'):
        json_data = get_row(id)
        return HttpResponse(json_data)

    if(request.method == 'DELETE'):
        result = delete_rows(id)
        return result

    if(request.method == 'PUT'):
        received_json_data = json.loads(request.body)

        result = update_row(id, received_json_data)
        return result

    return HttpResponse("ID is needed {}".format(id))


def createJSON(data):

    newData = []

    for record in data:

        datum = record.registration_date
        if(datum != None):
            datum = datum.strftime("%Y/%m/%d")

        new_dict = {
            "id": record.pk,
            "br_court_name": record.br_court_name,
            "kind_name": record.kind_name,
            "cin": record.cin,
            "registration_date": datum,
            "corporate_body_name": record.corporate_body_name,
            "br_section": record.br_section,
            "text": record.text,
            "street": record.street,
            "postal_code": record.postal_code,
            "city": record.city
        }

        newData.append(new_dict)

    return newData


def createJSONSingle(record):

    datum = record.registration_date
    if(datum != None):
        if isinstance(datum, str):
            datum = datum
        else:
            datum = datum.strftime("%Y/%m/%d")

    new_dict = {
        "id": record.pk,
        "br_court_name": record.br_court_name,
        "kind_name": record.kind_name,
        "cin": record.cin,
        "registration_date": datum,
        "corporate_body_name": record.corporate_body_name,
        "br_section": record.br_section,
        "text": record.text,
        "street": record.street,
        "postal_code": record.postal_code,
        "city": record.city
    }

    return new_dict


def metadata(GET, query):

    page = GET.get('page')
    if(page == None or page.isnumeric() == False):
        page = 1

    per_page = GET.get('per_page')
    if(per_page == None or per_page.isnumeric() == False):
        per_page = 10

    total = OrPodanieIssues.objects.filter(query).count()

    pages = math.ceil(int(total)/int(per_page))

    mdata = {
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "total": total
    }

    return mdata


def createQuery(GET):

    newQuery = Q()

    # QUERY
    quearyparam = GET.get('query')

    if(GET.get('query') != None):
        if(quearyparam.isnumeric()):
            newQuery &= Q(cin__contains=quearyparam)
        else:
            newQuery &= (Q(corporate_body_name__contains=quearyparam)
                         | Q(city__contains=quearyparam))

    # DATE
    dateGTE = GET.get('registration_date_gte')

    dateLTE = GET.get('registration_date_lte')

    if(dateGTE != None):
        try:
            dateGTE = parse(dateGTE)
            newQuery &= Q(registration_date__gte=dateGTE)
        except ValueError:
            dateGTE = None
    if(dateLTE != None):
        try:
            dateLTE = parse(dateLTE)
            newQuery &= Q(registration_date__lte=dateLTE)
        except ValueError:
            dateLTE = None

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

    # ORDER

    validOrders = ["id", "br_court_name", "kind_name", "cin", "registration_date",
                   "corporate_body_name", "br_section", "br_insertion", "text", "street", "postal_code", "city"]

    orderBy = GET.get('order_by')

    if orderBy not in validOrders:
        orderBy = None
    orderType = GET.get('order_type')

    if(orderBy != None):
        if (orderType == None or orderType == 'desc'):
            orderBy = "-{}".format(orderBy)
            result = OrPodanieIssues.objects.filter(newQuery).order_by(orderBy)[
                (page-1)*per_page:(page-1)*per_page+per_page]

        elif (orderType == 'asc'):
            result = OrPodanieIssues.objects.filter(newQuery).order_by(orderBy)[
                (page-1)*per_page:(page-1)*per_page+per_page]
    else:
        result = OrPodanieIssues.objects.filter(newQuery).order_by('-pk')[
            (page-1)*per_page:(page-1)*per_page+per_page]

    mdata = metadata(GET, newQuery)

    result = createJSON(result)

    data = {
        "items": result,
        "metadata": mdata
    }

    json_data = json.dumps(data)

    return json_data


def createINSERT(json_data):

    errorInJson = []

    # BULLETIN ISSUES INSERT
    today = datetime.now()
    bull_year = today.year
    bull_number = BulletinIssues.objects.filter(
        year=bull_year).aggregate(Max('number'))
    bull_number = bull_number['number__max']+1
    bull_published_at = today.strftime("%Y-%m-%d %H:%M:%S")

    newBullet = BulletinIssues(year=bull_year, number=bull_number,
                               published_at=bull_published_at, created_at=today, updated_at=today)
    newBullet.save()
    bull_id = newBullet.pk

    # RAW ISSUES INSERT
    newRaw = RawIssues(bulletin_issue=newBullet, file_name='-',
                       content='-', created_at=today, updated_at=today)
    newRaw.save()
    raw_id = newRaw.pk

    # OR_POADANIE_ISSUES_INSERT
    orpi_bull_id = bull_id
    orpi_raw_id = raw_id
    orpi_br_mark = "-"
    orpi_br_court_code = "-"

    if "br_court_name" in json_data.keys():
        orpi_br_court_name = json_data["br_court_name"]
    else:
        errors = {
            "field": "br_cout_name",
            "reason": "required"
        }
        errorInJson.append(errors)

    orpi_kind_code = "-"

    if "kind_name" in json_data.keys():
        orpi_kind_name = json_data["kind_name"]
    else:
        errors = {
            "field": "kind_name",
            "reason": "required"
        }
        errorInJson.append(errors)

    if "cin" in json_data.keys():
        if(isinstance(json_data["cin"], int)):
            orpi_cin = json_data["cin"]
        else:
            errors = {
                "field": "cin",
                "reason": "not_number"
            }
            errorInJson.append(errors)
    else:
        errors = {
            "field": "cin",
            "reason": "required"
        }
        errorInJson.append(errors)

    if "corporate_body_name" in json_data.keys():
        orpi_corporate_body_name = json_data["corporate_body_name"]
    else:
        errors = {
            "field": "corporate_body_name",
            "reason": "required"
        }
        errorInJson.append(errors)

    if "br_section" in json_data.keys():
        orpi_br_section = json_data["br_section"]
    else:
        errors = {
            "field": "br_section",
            "reason": "required"
        }
        errorInJson.append(errors)

    orpi_br_insertion = "-"

    if "text" in json_data.keys():
        orpi_text = json_data["text"]
    else:
        errors = {
            "field": "text",
            "reason": "required"
        }
        errorInJson.append(errors)

    if "street" not in json_data.keys():
        errors = {
            "field": "street",
            "reason": "required"
        }
        errorInJson.append(errors)
    else:
        orpi_street = json_data["street"]

    if "postal_code" not in json_data.keys():
        errors = {
            "field": "postal_code",
            "reason": "required"
        }
        errorInJson.append(errors)
    else:
        orpi_postal_code = json_data["postal_code"]

    if "city" not in json_data.keys():
        errors = {
            "field": "city",
            "reason": "required"
        }
        errorInJson.append(errors)
    else:
        orpi_city = json_data["city"]

    if "registration_date" in json_data.keys():
        checkdate = json_data["registration_date"]
        checkYear = checkdate.split("-")

        if(today.year == int(checkYear[0])):
            orpi_reg_date = json_data["registration_date"]
        else:
            errors = {
                "field": "registration_date",
                "reason": "invalid_range"
            }
            errorInJson.append(errors)

    else:
        errors = {
            "field": "registration_date",
            "reason": "required"
        }
        errorInJson.append(errors)

    if not errorInJson:

        orpi_address_line = "{}, {} {}".format(
            json_data["street"], json_data["postal_code"], json_data["city"])

        newOrPodanieIssues = OrPodanieIssues(created_at=today, updated_at=today, cin=orpi_cin, br_section=orpi_br_section, address_line=orpi_address_line, corporate_body_name=orpi_corporate_body_name, street=orpi_street, city=orpi_city, postal_code=orpi_postal_code, bulletin_issue=newBullet,
                                             raw_issue=newRaw, kind_code=orpi_kind_code, kind_name=orpi_kind_name, br_insertion=orpi_br_insertion, br_court_code=orpi_br_court_code, br_court_name=orpi_br_court_name, br_mark=orpi_br_mark, registration_date=orpi_reg_date, text=orpi_text)

        newOrPodanieIssues.save()

        newthing = createJSONSingle(newOrPodanieIssues)

        finalJson = {
            "response": newthing
        }

        finalJson = json.dumps(finalJson)

        return HttpResponse(finalJson, status=201)

    else:

        fullErrors = {
            "errors": errorInJson
        }

        fullErrors = json.dumps(fullErrors)

        return HttpResponse(fullErrors, status=422)


def delete_rows(id):

    try:
        delete_Issue = OrPodanieIssues.objects.get(pk=id)
    except OrPodanieIssues.DoesNotExist:
        result = {
            "error": {
                "message": "Záznam neexistuje"
            }
        }
        result = json.dumps(result)

        return HttpResponse(result, status=404)

    delete_bullet = delete_Issue.bulletin_issue
    delete_raw = delete_Issue.raw_issue

    delete_bullet.delete()
    delete_raw.delete()
    delete_Issue.delete()

    return HttpResponse(status=204)


def get_row(id):

    try:
        result = OrPodanieIssues.objects.get(pk=id)
    except OrPodanieIssues.DoesNotExist:
        result = {}
        json_data = {
            "response": result
        }
        json_data = json.dumps(json_data)
        return HttpResponse(json_data, status=200)

    result = createJSONSingle(result)

    json_data = {
        "response": result
    }

    json_data = json.dumps(json_data)

    return HttpResponse(json_data, status=200)


def update_row(id, json_data):

    listOfFields = []
    errorsInUpdate = []

    update_object = OrPodanieIssues.objects.get(pk=id)

    for i in json_data:
        listOfFields.append(i)

    if('br_court_name' in listOfFields):
        if(type(json_data['br_court_name']) == str):
            update_object.br_court_name = json_data['br_court_name']
        else:
            errors = {
                "field": "br_cout_name",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)

    if('kind_name' in listOfFields):
        if(type(json_data['kind_name']) == str):
            update_object.kind_name = json_data['kind_name']
        else:
            errors = {
                "field": "kind_name",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)

    if('cin' in listOfFields):
        if(isinstance(json_data['cin'], int)):
            update_object.cin = json_data['cin']
        else:
            errors = {
                "field": "cin",
                "reason": "not_number"
            }
            errorsInUpdate.append(errors)

    if('registration_date' in listOfFields):
        try:
            parse(json_data['registration_date'])

            today = datetime.now()
            check_year = today.year
            valueYear = json_data['registration_date'].split("-")
            if(check_year == int(valueYear[0])):
                update_object.registration_date = json_data['registration_date']
            else:
                errors = {
                    "field": "registration_date",
                    "reason": "invalid_range"
                }
                errorsInUpdate.append(errors)

        except ValueError:
            errors = {
                "field": "registration_date",
                "reason": "incorrect_date_value"
            }
            errorsInUpdate.append(errors)

    if('corporate_body_name' in listOfFields):
        if(type(json_data['corporate_body_name']) == str):
            update_object.corporate_body_name = json_data['corporate_body_name']
        else:
            errors = {
                "field": "corporate_body_name",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)

    if('br_section' in listOfFields):
        if(type(json_data['br_section']) == str):
            update_object.br_section = json_data['br_section']
        else:
            errors = {
                "field": "br_section",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)

    if('br_insertion' in listOfFields):
        if(type(json_data['br_insertion']) == str):
            update_object.br_insertion = json_data['br_insertion']
        else:
            errors = {
                "field": "br_insertion",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)

    if('text' in listOfFields):
        if(type(json_data['text']) == str):
            update_object.text = json_data['text']
        else:
            errors = {
                "field": "text",
                "reason": "not_string"
            }

    if('street' in listOfFields):
        if(type(json_data['street']) == str):
            update_object.street = json_data['street']
        else:
            errors = {
                "field": "street",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)

    if('postal_code' in listOfFields):
        if(type(json_data['postal_code']) == str):
            update_object.postal_code = json_data['postal_code']
        else:
            errors = {
                "field": "postal_code",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)

    if('city' in listOfFields):
        if(type(json_data['city']) == str):
            update_object.city = json_data['city']
        else:
            errors = {
                "field": "city",
                "reason": "not_string"
            }
            errorsInUpdate.append(errors)
    if not errorsInUpdate:

        update_object.save()
        data = createJSONSingle(update_object)
        updatedData = {
            "response": data
        }
        result = json.dumps(updatedData)

        return HttpResponse(result, status=201)
    else:
        fullErrors = {
            "errors": errorsInUpdate
        }
        fullErrors = json.dumps(fullErrors)
        return HttpResponse(fullErrors, status=422)
