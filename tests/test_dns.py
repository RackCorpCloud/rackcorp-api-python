import unittest
import rackcorpapi

# TODO unit test rackcorpapi.get_api_credentials()


class TestDNSDomainGetAll(unittest.TestCase):
    def setUp(self):

        # Initialize the API client with mock configuration
        self.client = rackcorpapi.Client(
            credential=rackcorpapi.ApiCredential(
                api_uuid="mock_api_uuid",
                api_secret="mock_api_secret",
            ),
            base_url="https://api.mock.rackcorp.net",
        )

    def test_dns_domain_getall(self):
        # Mock response data
        mock_response = [
            rackcorpapi.DnsDomain.from_dict({"id": 1, "name": "example.com"}),
            rackcorpapi.DnsDomain.from_dict({"id": 7, "name": "test.com"}),
        ]

        # Mock the API call
        def mock_getall():
            return mock_response

        self.client.dns.domain_getall = mock_getall

        # Call the method
        response = self.client.dns.domain_getall()

        # Assertions
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 2)
        self.assertIsInstance(response[0], rackcorpapi.DnsDomain)
        self.assertEqual(response[0].name, "example.com")
        self.assertEqual(response[1].id, 7)
