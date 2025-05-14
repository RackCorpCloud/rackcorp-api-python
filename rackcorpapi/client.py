from . import api, cred, dns
import platform


class Client:
    """
    Rackcorp API class to interact with the Rackcorp API.
    """

    def __init__(
        self,
        credential: cred.ApiCredential = None,
        base_url: str = "https://api.rackcorp.net/api/",
        api_version: str = "v2.8",
        user_agent: str = None,
    ):
        """
        Initialize the RackcorpApi class with an API credential

        :param cred: The API credentials
        """
        if credential is None:
            credential = cred.get_api_credentials()
        if credential is None:
            raise ValueError("Rackcorp API credentials are required")

        if not base_url.endswith("/"):
            base_url += "/"

        if user_agent is None:
            user_agent = f"rackcorpapi/0.1 python/{platform.python_version()}"

        self.api = api._api(
            cred=credential,
            base_url=base_url,
            api_version=api_version,
            user_agent=user_agent,
        )

        self.dns = dns._dnsOperations(self.api)
