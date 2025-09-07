import requests
from django.core.management.base import BaseCommand

from countries.models import Country, Region


class Command(BaseCommand):
    IMPORT_URL = "https://storage.googleapis.com/dcr-django-test/countries.json"
    help = f"Loads country data from the URL: {IMPORT_URL}"

    def get_data(self):
        response = requests.get(Command.IMPORT_URL)
        response.raise_for_status()
        data = response.json()
        return data

    def handle(self, *args, **options):
        data = self.get_data()
        for row in data:
            region, region_created = Region.objects.get_or_create(name=row["region"])
            if region_created:
                self.stdout.write(
                    self.style.SUCCESS("Region: {} - Created".format(region))
                )

            country, country_created = Country.objects.get_or_create(
                name=row["name"],
                defaults={
                    "alpha2Code": row["alpha2Code"],
                    "alpha3Code": row["alpha3Code"],
                    "population": row["population"],
                    "region": region,
                },
            )

            fields_to_update = [
                x
                for x in Country._meta.fields
                if not x.primary_key
                and x.name in row
                and getattr(country, x.name) != row[x.name]
                and row[x.name] is not None
            ]

            # Update country changes
            for field in fields_to_update:
                value = region if field.name == "region" else row.get(field.name)
                setattr(country, field.name, value)

            if not country_created or fields_to_update:
                country.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "{} - {}".format(
                        country, "Created" if country_created else "Updated"
                    )
                )
            )
