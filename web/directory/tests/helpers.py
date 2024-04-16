import json
from rest_framework.test import APIClient
from django.urls import reverse

def sanitize_response(response):
    """
    sanitize_response
    Responses of two requests run at different times, may contain the same data 
    but will not be identical. This function sanitizes the response to make them
    comparable to previous runs to aid in test cases. 
    """
    # Sort coop response list by the "name" key to ensure consistent ordering between tests.
    sorted_data = sorted(response.json(), key=lambda x: x["name"])
    # Responses should be identical except for rec_updated_date (depends on time it is run),
    #    and id (depends on order of tests). Removes those fields from response.
    modified_data = remove_keys_from_dict(sorted_data, ['rec_updated_date', 'id']) 
    # Structures response as JSON with sorted keys in a pretty-printed format.
    response_data = json.dumps(modified_data, indent=4, sort_keys=True)
    return response_data

def remove_keys_from_dict(obj, keys_to_remove):
    """
    Recursively remove specified keys from a dictionary, all its nested dictionaries,
    and any dictionaries within lists.
    """
    if isinstance(obj, dict):
        return {key: remove_keys_from_dict(value, keys_to_remove) 
                for key, value in obj.items() if key not in keys_to_remove}
    elif isinstance(obj, list):
        return [remove_keys_from_dict(item, keys_to_remove) for item in obj]
    else:
        return obj

def obtain_jwt_token(username, password):
    client = APIClient()
    response = client.post(reverse('token_obtain_pair'), {'username': username, 'password': password})
    if 'access' in response.data:
        return response.data['access']
    else:
        return None