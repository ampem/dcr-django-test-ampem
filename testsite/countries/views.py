from django.http import JsonResponse

from .models import Country, Region


def stats(_):
    regions = Region.objects.get_stats()
    response = {"regions": [region.to_dict() for region in regions]}

    return JsonResponse(response)


def detail(_, country_id=None, country_name=None):
    response = None
    try:
        countries = Country.objects
        if country_id:
            countries = countries.filter(id=country_id)
        elif country_name:
            countries = countries.filter(name__iexact=country_name)
        country = countries.get()
        response = JsonResponse({"country": country.to_dict()})
    except Country.DoesNotExist:
        response = JsonResponse({"error": "Country not found"}, status=404)

    return response
