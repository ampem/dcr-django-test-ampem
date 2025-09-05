from django.test import TestCase, Client
from django.urls import reverse
from django.db.models import Sum, Count
from unittest.mock import patch
from countries.models import Region, Country, RegionStats

class CountryStatsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.stats_url = '/countries/stats/'

    # Unit Test: Test RegionStats to_dict
    def test_region_stats_to_dict(self):
        region_stats = RegionStats(name='Africa', number_countries=54, total_population=1000000)
        expected = {
            'name': 'Africa',
            'number_countries': 54,
            'total_population': 1000000,
        }
        self.assertEqual(region_stats.to_dict(), expected)

    # Unit Test: Test RegionQuerySet get_stats
    @patch('countries.models.RegionQuerySet.values')
    def test_region_queryset_get_stats(self, mock_values):
        mock_values.return_value.order_by.return_value = [
            {'name': 'Africa', 'number_countries': 54, 'total_population': 1000000},
            {'name': 'Americas', 'number_countries': 35, 'total_population': 500000},
        ]
        stats = Region.objects.get_stats()
        self.assertEqual(len(stats), 2)
        self.assertIsInstance(stats[0], RegionStats)
        self.assertEqual(stats[0].name, 'Africa')
        self.assertEqual(stats[0].number_countries, 54)
        self.assertEqual(stats[0].total_population, 1000000)
        self.assertEqual(stats[1].name, 'Americas')
        self.assertEqual(stats[1].number_countries, 35)
        self.assertEqual(stats[1].total_population, 500000)

    # Unit Test: Test RegionQuerySet get_stats with NULL population
    @patch('countries.models.RegionQuerySet.values')
    def test_region_queryset_get_stats_null_population(self, mock_values):
        mock_values.return_value.order_by.return_value = [
            {'name': 'Africa', 'number_countries': 0, 'total_population': None},
        ]
        stats = Region.objects.get_stats()
        self.assertEqual(len(stats), 1)
        self.assertIsInstance(stats[0], RegionStats)
        self.assertEqual(stats[0].name, 'Africa')
        self.assertEqual(stats[0].number_countries, 0)
        self.assertEqual(stats[0].total_population, 0)

    # Unit Test: Test RegionManager to_dict
    @patch('countries.models.RegionQuerySet.values')
    def test_region_manager_to_dict(self, mock_values):
        mock_values.return_value.order_by.return_value = [
            {'name': 'Africa', 'number_countries': 54, 'total_population': 1000000},
            {'name': 'Americas', 'number_countries': 35, 'total_population': 500000},
        ]
        result = Region.objects.to_dict()
        expected = {
            'regions': [
                {'name': 'Africa', 'number_countries': 54, 'total_population': 1000000},
                {'name': 'Americas', 'number_countries': 35, 'total_population': 500000},
            ]
        }
        self.assertEqual(result, expected)

    # Unit Test: Test stats view
    @patch('countries.models.Region.objects.get_stats')
    def test_stats_view(self, mock_get_stats):
        mock_get_stats.return_value = [
            RegionStats(name='Africa', number_countries=54, total_population=1000000),
            RegionStats(name='Americas', number_countries=35, total_population=500000),
        ]
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, 200)
        expected_data = {
            'regions': [
                {'name': 'Africa', 'number_countries': 54, 'total_population': 1000000},
                {'name': 'Americas', 'number_countries': 35, 'total_population': 500000},
            ]
        }
        self.assertEqual(response.json(), expected_data)

    # Unit Test: Test stats view with empty data
    @patch('countries.models.Region.objects.get_stats')
    def test_stats_view_empty(self, mock_get_stats):
        mock_get_stats.return_value = []
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'regions': []})
