import requests
from fake_useragent import UserAgent
from functools import lru_cache
import random
import time

@lru_cache(maxsize=1)
def get_user_agent():
    return UserAgent()

def get_rental_detail(rental_id, retries=3, backoff_factor=0.3):
    ua = get_user_agent()
    headers = {"User-Agent": ua.random}
    
    session = requests.Session()
    
    for attempt in range(retries):
        try:
            initial_url = f"https://rent.591.com.tw/home/{rental_id}"
            response = session.get(initial_url, headers=headers, timeout=10)
            response.raise_for_status()

            cookies = session.cookies.get_dict()
            headers.update({
                "deviceid": cookies.get("T591_TOKEN"),
                "device": "pc",
                "X-CSRF-TOKEN": cookies.get("XSRF-TOKEN")
            })

            detail_url = f"https://bff.591.com.tw/v1/house/rent/detail?id={rental_id}"
            response = session.get(detail_url, headers=headers, timeout=10)
            response.raise_for_status()

            return response.json().get("data")

        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 0.1)
            time.sleep(wait_time)

    return None