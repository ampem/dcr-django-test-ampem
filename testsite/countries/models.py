from dataclasses import dataclass
from typing import Dict, List

from django.db import models
from django.db.models import Count, Sum
from django.db.models.query import QuerySet


@dataclass
class RegionStats:
    name: str
    number_countries: int
    total_population: int

    def to_dict(self) -> Dict[str, int | str]:
        return {
            "name": self.name,
            "number_countries": self.number_countries,
            "total_population": self.total_population,
        }


class RegionQuerySet(QuerySet):
    def get_stats(self) -> List[RegionStats]:
        queryset = (
            self.annotate(
                number_countries=Count("countries"),
                total_population=Sum("countries__population"),
            )
            .values("name", "number_countries", "total_population")
            .order_by("name")
        )
        return [
            RegionStats(
                name=region["name"],
                number_countries=region["number_countries"],
                total_population=region["total_population"] or 0,
            )
            for region in queryset
        ]


class RegionManager(models.Manager):
    def get_queryset(self) -> RegionQuerySet:
        return RegionQuerySet(self.model, using=self._db)

    def get_stats(self) -> List[RegionStats]:
        return self.get_queryset().get_stats()

    def to_dict(self) -> Dict[str, List[Dict[str, int | str]]]:
        return {"regions": [region.to_dict() for region in self.get_stats()]}


class Region(models.Model):
    objects = RegionManager()
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)


class TopLevelDomain(models.Model):
    name = models.CharField(max_length=63 + 1, unique=True)

    def __str__(self):
        return str(self.name)


class Country(models.Model):
    name = models.CharField(max_length=100)
    alpha2Code = models.CharField(max_length=2)
    alpha3Code = models.CharField(max_length=3)
    population = models.IntegerField()
    capital = models.CharField(blank=True, default="", max_length=100, null=False)

    region = models.ForeignKey(
        "Region",
        on_delete=models.CASCADE,
        related_name="countries",
    )

    topLevelDomain = models.ManyToManyField(TopLevelDomain, blank=True)

    def to_dict(self) -> Dict[str, int | str | List[str]]:
        return {
            "name": self.name,
            "alpha2Code": self.alpha2Code,
            "alpha3Code": self.alpha3Code,
            "population": self.population,
            "capital": self.capital,
            "region": self.region.name,
            "topLevelDomain": [
                topLevelDomain.name for topLevelDomain in self.topLevelDomain.all()
            ],
        }

    def __str__(self):
        return str(self.name)
