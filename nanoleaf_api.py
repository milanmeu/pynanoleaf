import logging
import requests

logger = logging.getLogger(__name__)


class Nanoleaf(object):
    """Nanoleaf API wrapper"""
    def __init__(self, host, token=None, port=16021, protocol='http'):
        self.host = host
        self.token = token
        self.port = port
        self.protocol = protocol
        self._session = requests.Session()

    @property
    def baseUrl(self):
        return '{}://{}:{}/api/v1/'.format(
            self.protocol, self.host, self.port)

    @property
    def authenticatedUrl(self):
        return '{}{}/'.format(self.baseUrl, self.token)

    @property
    def available(self):
        "Returns True if the Nanoleaf device is available"
        try:
            self.info
        except Exception:
            return False
        return True

    @property
    def info(self):
        return self._request("/", 'GET').json()

    def add_user(self):
        response = self._request("new", 'POST', authenticated=False).json()
        return response['auth_token']

    def authenticate(self):
        token = self.add_user()
        self.token = token

    def delete_user(self):
        return self._request("/", 'DELETE')

    @property
    def on(self):
        response = self._request("state/on", 'GET').json()
        return response['value']

    @on.setter
    def on(self, value: bool):
        data = {"on": {"value": value}}
        self._request("state", 'PUT', data)

    @property
    def off(self):
        response = self._request("state/on", 'GET').json()
        return not response['value']

    @off.setter
    def off(self, value: bool):
        data = {"on": {"value": not value}}
        self._request("state", 'PUT', data)

    @property
    def brightness(self):
        response = self._request("state/brightness", 'GET').json()
        return response['value']

    @property
    def max_brightness(self):
        response = self._request("state/brightness", 'GET').json()
        return response['max']

    @property
    def min_brightness(self):
        response = self._request("state/brightness", 'GET').json()
        return response['min']

    @brightness.setter
    def brightness(self, value: int):
        data = {"brightness": {"value": value}}
        self._request("state", 'PUT', data)

    def brightness_transition(self, value: int, duration: int):
        """Sets the brightness to the specified value
        with a transition lastind duration seconds"""
        data = {"brightness": {"value": value, "duration": duration}}
        self._request("state", 'PUT', data)

    def brightness_increment(self, increment: int):
        "Lowers or raises the brightness by the specified increment"
        data = {"brightness": {"increment": increment}}
        self._request("state", 'PUT', data)

    def _request(self, path, method=None, data=None, authenticated=True):
        if authenticated:
            url = self.authenticatedUrl + path
        else:
            url = self.baseUrl + path
        try:
            req = requests.Request(method, url, json=data)
            response = self._session.send(req.prepare())
            response.raise_for_status()
            if response.status_code == 200:
                logger.info(response.json())
            return (response)
        except(requests.ConnectionError, requests.Timeout) as e:
            raise Unavailable("{} is not available".format(self.host)) from e
        except(requests.HTTPError) as e:
            if e.response.status_code == 400:
                raise NanoleafError("Bad Request sent") from e
            elif e.response.status_code == 401:
                raise InvalidToken("Invalid Token for {}"
                                   .format(self.host)) from e
            elif e.response.status_code == 403:
                raise NotAuthorizingNewTokens(
                    """Nanoleaf is not allowing new tokens,
                    please make sure to press and hold the on/off button
                    on your device for 5 seconds until the LED starts flashing
                    in a pattern.""") from e
            elif e.response.status_code == 404:
                raise Unavailable("{} returns 404".format(url)) from e
            else:
                raise NanoleafError("Unknown Error occured") from e


class NanoleafError(Exception):
    def __init__(self, message):
        self.message = message
        logger.error(message)


class Unavailable(NanoleafError):
    pass


class NotAuthorizingNewTokens(NanoleafError):
    pass


class InvalidToken(NanoleafError):
    pass
