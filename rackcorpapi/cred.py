import requests
import requests.auth
import configparser
import os


class ApiCredential:
    """
    Rackcorp API credentials class to hold API key and secret.
    """

    def __init__(self, api_uuid: str, api_secret: str):
        """
        Initialize the ApiCredential class with API uuid and secret.

        :param api_uuid: The API key uuid for authentication.
        :param api_secret: The API key secret for authentication.
        """
        self.api_uuid = api_uuid
        self.api_secret = api_secret

    def http_basic_auth(self) -> requests.auth.HTTPBasicAuth:
        """
        Get HTTP Basic Authentication for the API credentials.

        :return: An instance of HTTPBasicAuth with the API credentials.
        """
        return requests.auth.HTTPBasicAuth(self.api_uuid, self.api_secret)


def get_api_credentials() -> ApiCredential:
    """
    Find API credentials in the execution environment.
    :return: An instance of RackcorpApiCredential with loaded credentials or None.
    """
    api_uuid = os.getenv("RACKCORP_API_UUID", "").strip()
    api_secret = os.getenv("RACKCORP_API_SECRET", "").strip()
    if api_uuid and api_secret:
        return ApiCredential(api_uuid, api_secret)

    config_paths = [
        os.path.expanduser("~/.rackcorp"),
        os.path.expanduser("~/.config/rackcorp/config"),
    ]
    for path in config_paths:
        if os.path.exists(path):
            config = configparser.ConfigParser()
            config.read(path)
            if config and "general" in config:
                api_uuid = config["general"].get("apiuuid", "").strip()
                api_secret = config["general"].get("apisecret", "").strip()
                if api_uuid and api_secret:
                    return ApiCredential(api_uuid, api_secret)

    return None
