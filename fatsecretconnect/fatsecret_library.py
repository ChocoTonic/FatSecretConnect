import json
import os
from datetime import datetime, timedelta
from functools import wraps
from pprint import pprint
from time import sleep
from typing import *

import pytz
import requests
from bs4 import BeautifulSoup
from fatsecret import Fatsecret
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class FatSecret_Library:
    def __init__(self):
        self.fs = None
        self.is_authenticated = False
        self.session = None

    def requests_session(self) -> requests.sessions.Session:
        """establish a session with retry

        Returns:
            requests session: a requests session
        """
        s = requests.Session()

        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )

        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.mount("http://", HTTPAdapter(max_retries=retries))

        return s

    def fs_authenticate(
        self,
        fs_username: str,
        fs_password: str,
        consumer_key: str,
        consumer_secret: str,
    ) -> Fatsecret:
        """User Authentication using credentials

        Returns:
            Fatsecret: Fatsecret object
        """

        print(f"Authenticating...")

        # make session
        self.session = self.requests_session()

        self.fs = Fatsecret(consumer_key=consumer_key, consumer_secret=consumer_secret)

        try:
            auth_url = self.fs.get_authorize_url()

            # replace text to match required URL in payload send
            auth_url = auth_url.replace("authorize", "authorize.aspx")
            print(f"{auth_url = }")

            # payload to autofill site
            payload = {
                "__VIEWSTATE": "NEaqHq4+9PA2+EibNksxj9klblmFlVWx/HeM0gFBhuvFXAZCj//UwAtEQXUi9oMv1/hyQJbS/QWgdrU+SeVWND+aoX0L8/hkhxXIByB2H1AZrD/Z/oQvtNPgAWYotS65vICPfDijPxwhjdAoRof1V5zlpoQBc5U9DjptmInVeh8upOxE",
                "__VIEWSTATEGENERATOR": "E738DFBB",
                "Name": fs_username,
                "Login.x": 0,
                "Login.y": 0,
                "Password": fs_password,
            }

            # send payload
            pin_html_raw = self.session.post(url=auth_url, data=payload)

            # parse with lxml
            pin_html_parsed = BeautifulSoup(pin_html_raw.content, "lxml")

            # pin is in the first b tag
            auth_pin = pin_html_parsed.find("b").text.strip()
            print(f"{auth_pin = }")

            # establish session token from authentication
            self.fs.authenticate(auth_pin)
            # print(f"Authenticated as {fs_username}!")
            # print()
            # print(type(self.fs))

            self.is_authenticated = True

            return self.fs

        except Exception as e:
            print(f"Authentication failed!")
            print(f"{e = }")
            print()

    def check_authenticated(self) -> bool:
        return self.is_authenticated

    def food_entries_get_month_w_error_checking(self, date_time: datetime) -> dict:
        """This function retrieves a month's worth of food entries from the 'fs' attribute, which is expected to be an instance of a class with a 'food_entries_get_month' method that takes a 'date' argument. The retrieved entries are returned in the form of a list of dictionaries, where each dictionary represents a food entry.

        If a KeyError is encountered when attempting to retrieve the entries, an empty 'entries_month' dict is returned and a message is printed to indicate the error.

        If the retrieved entries are not in the form of a list, they are converted to a list before being returned.

        The function also checks if the current date is already present in the retrieved entries, if not it adds a placeholder dict to the list.

        Args:
            date_time (datetime): date to retrieve food entries for that month. Works for any day in that month.

        Returns:
            entries_month (List[Dict]): list of dicts containing food entries for the month
        """
        print("getting month's entries...")

        fs = self.fs
        entries_month = {}
        try:
            entries_month = fs.food_entries_get_month(date=date_time)
        except KeyError as e:
            print(f"KeyError: {e}. Returning empty entries_month.")

        if type(entries_month) is dict:
            entries_month = [entries_month]

        pprint(entries_month)

        date_int = fs.unix_time(date_time)

        is_found = False
        for entry in entries_month:
            if entry.get("date_int") == str(date_int):
                is_found = True
                break

        # check if date_int is already in entries_month
        if not is_found:
            print("Could not find date_int in entries_month, adding placeholder dict.")

            # append this dict to entries_month
            entries_month.append(
                {
                    "calories": "0",
                    "carbohydrate": "0",
                    "date_int": str(date_int),
                    "fat": "0",
                    "protein": "0",
                }
            )

        return entries_month

    def convert_unix_to_datetime(unix_date: int) -> datetime:
        date_epoch = datetime(1970, 1, 1, 0, 0)
        new_datetime = date_epoch + timedelta(unix_date)
        return new_datetime

    def get_datetime_now(self) -> datetime:
        tz_LA = pytz.timezone("America/Los_Angeles")
        # remove timezone information
        return datetime.now(tz_LA).replace(tzinfo=None)

    def get_current_file_name() -> str:
        # Get the base name of the current script file
        base_name = os.path.basename(__file__)

        # Split the file name by the dot (.) and keep the first part
        file_name = os.path.splitext(base_name)[0]

        return file_name

    def get_fs(self) -> Fatsecret:
        return self.fs

    def __str__(self):
        return f"FatSecret_Library()"

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def retry(
        exception_type,
        max_attempts=10,
        initial_delay=5,
        backoff_factor=1.5,
    ) -> Callable[..., Any]:
        """Retry calling the decorated function using an exponential backoff.

        http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

        This decorator allows the decorated function to be retried in case of specific exceptions,
        employing an exponential backoff strategy.

        Args:
            ExceptionToCheck (Union[Type[BaseException], Tuple[Type[BaseException], ...]]):
                The exception(s) to check. It can be a single exception or a tuple of exceptions.
            tries (int, optional): Number of attempts before giving up. Defaults to 10.
            delay (int, optional): Initial delay between retries in seconds. Defaults to 5.
            backoff (float, optional): Backoff multiplier; each retry increases delay. Defaults to 1.5.

        Returns:
            Callable: Decorated function with retry mechanism.
        """

        def deco_retry(f: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(f)
            def f_retry(*args: Tuple[Any, ...], **kwargs: Any) -> Any:
                mtries, mdelay = max_attempts, initial_delay
                while mtries > 1:
                    try:
                        return f(*args, **kwargs)
                    except exception_type as e:
                        msg = f"{e}, Retrying in {mdelay} seconds..."

                        print(msg)
                        sleep(mdelay)

                        mtries = mtries - 1
                        mdelay = mdelay * backoff_factor
                return f(*args, **kwargs)

            return f_retry  # true decorator

        return deco_retry


def main():
    logins_json_path = os.path.join(
        r"/home/asdf/General/Python/TDEEFatSecretGoogleSheet/src/common/logins.json"
    )

    with open(logins_json_path, "r") as f:
        FS_CREDENTIALS = json.load(f)

    fs_lib = FatSecret_Library()

    fs_lib.fs_authenticate(
        fs_username=FS_CREDENTIALS["test"]["fs_username"],
        fs_password=FS_CREDENTIALS["test"]["fs_password"],
        consumer_key=FS_CREDENTIALS["test"]["fs_consumer_key"],
        consumer_secret=FS_CREDENTIALS["test"]["fs_consumer_secret"],
    )

    print(f"{fs_lib = }")

    fs = fs_lib.get_fs()
    print(fs)


if __name__ == "__main__":
    main()
