import requests
from django.conf import settings
from django.core.cache import cache

# NubAPI URLs
BANKS_URL = "https://nubapi.com/banks"
VERIFY_ACCOUNT_URL = "https://nubapi.com/api/verify"

def fetch_bank_codes():
    """
    Fetch bank codes and names from NubAPI and cache them for faster access.
    Returns a dictionary of bank codes and names, sorted alphabetically by bank name.
    """
    cache_key = "bank_codes"
    cached_data = cache.get(cache_key)

    if cached_data:
        # Ensure cached data is already sorted
        return dict(sorted(cached_data.items(), key=lambda x: x[1]))

    try:
        response = requests.get(BANKS_URL, timeout=10)
        response.raise_for_status()
        bank_codes = response.json()
        
        # Sort the dictionary by bank name before caching
        sorted_bank_codes = dict(sorted(bank_codes.items(), key=lambda x: x[1]))

        # Cache the sorted dictionary for 24 hours (86400 seconds)
        cache.set(cache_key, sorted_bank_codes, timeout=86400)
        return sorted_bank_codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bank codes: {e}")
        return {}
def verify_account_details(account_number, bank_code):
    """
    Verify an account using the NubAPI.
    Returns the account details or an empty dictionary if an error occurs.
    """
    headers = {"Authorization": f"Bearer {settings.NUBAPI_API_KEY}"}  # Fetch API key from settings
    payload = {
        "account_number": account_number,
        "bank_code": bank_code,
    }
    try:
        response = requests.get(VERIFY_ACCOUNT_URL, headers=headers, params=payload, timeout=10)
        response.raise_for_status()
        return response.json()  # Account details
    except requests.exceptions.RequestException as e:
        print(f"Error verifying account details: {e}")
        return {}
