from unittest.mock import patch

from django.test import Client, TestCase

from countries.models import Country, Region, RegionStats, TopLevelDomain


class CountryViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.stats_url = "/countries/stats/"
        self.region = Region.objects.create(name="Africa")
        self.tld = TopLevelDomain.objects.create(name=".com")
        self.country = Country.objects.create(
            name="Nigeria",
            alpha2Code="NG",
            alpha3Code="NGA",
            population=200000,
            capital="Abuja",
            region=self.region,
        )
        self.country.topLevelDomain.add(self.tld)
        self.detail_url_by_id = f"/countries/id:{self.country.id}/"
        self.detail_url_by_name = f"/countries/name:{self.country.name}/"

    # Unit Test: Test RegionStats to_dict
    def test_region_stats_to_dict(self):
        region_stats = RegionStats(
            name="Africa", number_countries=54, total_population=1000000
        )
        expected = {
            "name": "Africa",
            "number_countries": 54,
            "total_population": 1000000,
        }
        self.assertEqual(region_stats.to_dict(), expected)

    # Unit Test: Test RegionQuerySet get_stats
    @patch("countries.models.RegionQuerySet.values")
    def test_region_queryset_get_stats(self, mock_values):
        mock_values.return_value.order_by.return_value = [
            {"name": "Africa", "number_countries": 54, "total_population": 1000000},
            {"name": "Americas", "number_countries": 35, "total_population": 500000},
        ]
        stats = Region.objects.get_stats()
        self.assertEqual(len(stats), 2)
        self.assertIsInstance(stats[0], RegionStats)
        self.assertEqual(stats[0].name, "Africa")
        self.assertEqual(stats[0].number_countries, 54)
        self.assertEqual(stats[0].total_population, 1000000)
        self.assertEqual(stats[1].name, "Americas")
        self.assertEqual(stats[1].number_countries, 35)
        self.assertEqual(stats[1].total_population, 500000)

    # Unit Test: Test RegionQuerySet get_stats with NULL population
    @patch("countries.models.RegionQuerySet.values")
    def test_region_queryset_get_stats_null_population(self, mock_values):
        mock_values.return_value.order_by.return_value = [
            {"name": "Africa", "number_countries": 0, "total_population": None},
        ]
        stats = Region.objects.get_stats()
        self.assertEqual(len(stats), 1)
        self.assertIsInstance(stats[0], RegionStats)
        self.assertEqual(stats[0].name, "Africa")
        self.assertEqual(stats[0].number_countries, 0)
        self.assertEqual(stats[0].total_population, 0)

    # Unit Test: Test RegionQuerySet get_stats with real data
    def test_region_queryset_get_stats_real_data(self):
        # Create additional data
        country2 = Country.objects.create(  # pylint: disable=unused-variable
            name="Ghana",
            alpha2Code="GH",
            alpha3Code="GHA",
            population=30000,
            capital="Accra",
            region=self.region,
        )
        stats = Region.objects.get_stats()
        self.assertEqual(len(stats), 1)
        self.assertIsInstance(stats[0], RegionStats)
        self.assertEqual(stats[0].name, "Africa")
        self.assertEqual(stats[0].number_countries, 2)
        self.assertEqual(stats[0].total_population, 230000)  # 200000 + 30000

    # Unit Test: Test RegionManager to_dict
    @patch("countries.models.RegionQuerySet.values")
    def test_region_manager_to_dict(self, mock_values):
        mock_values.return_value.order_by.return_value = [
            {"name": "Africa", "number_countries": 54, "total_population": 1000000},
            {"name": "Americas", "number_countries": 35, "total_population": 500000},
        ]
        result = Region.objects.to_dict()
        expected = {
            "regions": [
                {"name": "Africa", "number_countries": 54, "total_population": 1000000},
                {
                    "name": "Americas",
                    "number_countries": 35,
                    "total_population": 500000,
                },
            ]
        }
        self.assertEqual(result, expected)

    # Unit Test: Test stats view
    @patch("countries.models.Region.objects.get_stats")
    def test_stats_view(self, mock_get_stats):
        mock_get_stats.return_value = [
            RegionStats(name="Africa", number_countries=54, total_population=1000000),
            RegionStats(name="Americas", number_countries=35, total_population=500000),
        ]
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "regions": [
                {"name": "Africa", "number_countries": 54, "total_population": 1000000},
                {
                    "name": "Americas",
                    "number_countries": 35,
                    "total_population": 500000,
                },
            ]
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test stats view with empty data
    @patch("countries.models.Region.objects.get_stats")
    def test_stats_view_empty(self, mock_get_stats):
        mock_get_stats.return_value = []
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"regions": []})

    # Unit Test: Test country detail view by ID
    def test_country_detail_view_by_id(self):
        response = self.client.get(self.detail_url_by_id)
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Nigeria",
                "alpha2Code": "NG",
                "alpha3Code": "NGA",
                "population": 200000,
                "capital": "Abuja",
                "region": "Africa",
                "topLevelDomain": [".com"],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test country detail view by name
    def test_country_detail_view_by_name(self):
        response = self.client.get(self.detail_url_by_name)
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Nigeria",
                "alpha2Code": "NG",
                "alpha3Code": "NGA",
                "population": 200000,
                "capital": "Abuja",
                "region": "Africa",
                "topLevelDomain": [".com"],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test country detail view by ID for non-existent country
    def test_country_detail_view_by_id_not_found(self):
        response = self.client.get("/countries/id:999/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Country not found"})

    # Unit Test: Test country detail view by name for non-existent country
    def test_country_detail_view_by_name_not_found(self):
        response = self.client.get("/countries/name:NonExistentCountry/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Country not found"})

    # Unit Test: Test country detail view by ID with no top-level domains
    def test_country_detail_view_by_id_no_tlds(self):
        # Create a country with no top-level domains
        country_no_tld = Country.objects.create(
            name="Ghana",
            alpha2Code="GH",
            alpha3Code="GHA",
            population=30000,
            capital="Accra",
            region=self.region,
        )
        response = self.client.get(f"/countries/id:{country_no_tld.id}/")
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Ghana",
                "alpha2Code": "GH",
                "alpha3Code": "GHA",
                "population": 30000,
                "capital": "Accra",
                "region": "Africa",
                "topLevelDomain": [],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test country detail view by name with no top-level domains
    def test_country_detail_view_by_name_no_tlds(self):
        # Create a country with no top-level domains
        country_no_tld = Country.objects.create(
            name="Ghana",
            alpha2Code="GH",
            alpha3Code="GHA",
            population=30000,
            capital="Accra",
            region=self.region,
        )
        response = self.client.get(f"/countries/name:{country_no_tld.name}/")
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Ghana",
                "alpha2Code": "GH",
                "alpha3Code": "GHA",
                "population": 30000,
                "capital": "Accra",
                "region": "Africa",
                "topLevelDomain": [],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test country detail view by ID with empty capital
    def test_country_detail_view_by_id_empty_capital(self):
        # Create a country with an empty capital
        country_empty_capital = Country.objects.create(
            name="Namibia",
            alpha2Code="NA",
            alpha3Code="NAM",
            population=25000,
            capital="",
            region=self.region,
        )
        response = self.client.get(f"/countries/id:{country_empty_capital.id}/")
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Namibia",
                "alpha2Code": "NA",
                "alpha3Code": "NAM",
                "population": 25000,
                "capital": "",
                "region": "Africa",
                "topLevelDomain": [],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test country detail view by name with empty capital
    def test_country_detail_view_by_name_empty_capital(self):
        # Create a country with an empty capital
        country_empty_capital = Country.objects.create(
            name="Namibia",
            alpha2Code="NA",
            alpha3Code="NAM",
            population=25000,
            capital="",
            region=self.region,
        )
        response = self.client.get(f"/countries/name:{country_empty_capital.name}/")
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Namibia",
                "alpha2Code": "NA",
                "alpha3Code": "NAM",
                "population": 25000,
                "capital": "",
                "region": "Africa",
                "topLevelDomain": [],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test country detail view by ID with multiple TLDs
    def test_country_detail_view_by_id_multiple_tlds(self):
        # Create additional TLD
        tld2 = TopLevelDomain.objects.create(name=".org")
        self.country.topLevelDomain.add(tld2)
        response = self.client.get(self.detail_url_by_id)
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Nigeria",
                "alpha2Code": "NG",
                "alpha3Code": "NGA",
                "population": 200000,
                "capital": "Abuja",
                "region": "Africa",
                "topLevelDomain": [".com", ".org"],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test country detail view by name case-insensitive
    def test_country_detail_view_by_name_case_insensitive(self):
        response = self.client.get("/countries/name:nigeria/")
        self.assertEqual(response.status_code, 200)
        expected_data = {
            "country": {
                "name": "Nigeria",
                "alpha2Code": "NG",
                "alpha3Code": "NGA",
                "population": 200000,
                "capital": "Abuja",
                "region": "Africa",
                "topLevelDomain": [".com"],
            }
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test Region __str__
    def test_region_str(self):
        self.assertEqual(str(self.region), "Africa")

    # Unit Test: Test TopLevelDomain __str__
    def test_topleveldomain_str(self):
        self.assertEqual(str(self.tld), ".com")
