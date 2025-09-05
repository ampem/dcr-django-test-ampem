from django.http import JsonResponse
from .models import Region

def stats(request):
    # TODO - Provide name, number_countries and total_population for each region
    regions = Region.objects.get_stats()
    response = {"regions": [region.to_dict() for region in regions]}

    return JsonResponse(response)
