import unittest
import rackcorpapi

# TODO unit test rackcorpapi.get_api_credentials()


class TestDNSDomainGetAll(unittest.TestCase):
    def setUp(self):

        # Initialize the API client with mock configuration
        self.api = rackcorpapi.Client(
            cred=rackcorpapi.ApiCredential(
                api_uuid="mock_api_uuid",
                api_secret="mock_api_secret",
            ),
            base_url="https://api.mock.rackcorp.net",
        )

    def test_dns_domain_getall(self):
        # Mock response data
        mock_response = [
            {"id": 1, "domain": "example.com", "status": "active"},
            {"id": 2, "domain": "test.com", "status": "inactive"},
        ]

        # Mock the API call
        def mock_getall():
            return mock_response

        self.api.dns_domain_getall = mock_getall

        # Call the method
        response = self.api.dns_domain_getall()

        # Assertions
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["domain"], "example.com")
        self.assertEqual(response[1]["status"], "inactive")


if __name__ == "__main__":
    unittest.main()
