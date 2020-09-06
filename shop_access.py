import requests
import logging
import json

from environs import Env

env = Env()
env.read_env()

client_id = env('CLIENT_ID')
client_secret = env('CLIENT_SECRET_TOKEN')

logging.basicConfig(format="%(process)d %(levelname)s %(message)s", level=logging.WARNING)


def _get_access_token(client_id, client_secret):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    url = 'https://api.moltin.com/oauth/access_token'

    response = requests.post(url, data=data)
    response.raise_for_status()
    access_response = response.json()

    return access_response['access_token']


def _get_bearer_access_token(client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit'
    }

    url = 'https://api.moltin.com/oauth/access_token'

    response = requests.post(url, data=data)
    response.raise_for_status()
    access_response = response.json()

    return access_response['access_token']


def add_product_to_cart(product_id, client_id, quantity, chat_id):
    bearer_access_token = _get_bearer_access_token(client_id=client_id)

    product_data = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": int(quantity),
            }
        }

    headers = {
        'Authorization': f'Bearer {bearer_access_token}',
        'Content-Type': 'application/json',
    }

    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'

    response = requests.post(url, headers=headers, data=json.dumps(product_data))
    response.raise_for_status()


def get_cart_items(client_id, chat_id):
    bearer_access_token = _get_bearer_access_token(client_id=client_id)

    headers = {
        'Authorization': f'Bearer {bearer_access_token}',
    }

    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    cart = response.json()
    items =[]

    total_amount = cart['meta']['display_price']['with_tax']['formatted']

    for item in cart['data']:
        items.append({
            'name': item['name'],
            'id': item['id'],
            'description': item['description'],
            'price': item['meta']['display_price']['with_tax']['unit']['formatted'],
            'quantity': item['quantity'],
            'amount': item['meta']['display_price']['with_tax']['value']['formatted'],
        })

    return items, total_amount


def get_products_list(client_id):
    bearer_access_token = _get_bearer_access_token(client_id=client_id)
    
    headers = {
        'Authorization': f'Bearer {bearer_access_token}',
        'Content-Type': 'application/json',
    }

    url = 'https://api.moltin.com/v2/products/'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    products_response = response.json()

    return products_response['data']


def get_product_by_id(client_id, product_id):
    bearer_access_token = _get_bearer_access_token(client_id=client_id)
    
    headers = {
        'Authorization': f'Bearer {bearer_access_token}',
        'Content-Type': 'application/json',
    }

    url = f'https://api.moltin.com/v2/products/{product_id}'

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    product= response.json()['data']

    return {
        'name' : product['name'],
        'description': product['description'],
        'stock': product['meta']['stock']['level'],
        'price': product['meta']['display_price']['with_tax']['formatted'],
        'image_id': product['relationships']['main_image']['data']['id']
    }


def get_image_url(client_id, image_id):
    bearer_access_token = _get_bearer_access_token(client_id=client_id)
    headers = {
        'Authorization': f'Bearer {bearer_access_token}',
    }

    url = f'https://api.moltin.com/v2/files/{image_id}'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    image = response.json()

    return image['data']['link']['href']


def remove_cart_items(client_id, chat_id, product_id):
    bearer_access_token = _get_bearer_access_token(client_id=client_id)

    headers = {
        'Authorization': f'Bearer {bearer_access_token}',
    }
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items/{product_id}'

    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def create_customer(client_id, username, email, password):
    bearer_access_token = _get_bearer_access_token(client_id=client_id)

    headers = {
        'Authorization': f'Bearer {bearer_access_token}',
        'Content-Type': 'application/json',
    }

    data = { 
        "data": { 
            "type": "customer", 
            "name": username, 
            "email": email, 
            "password": password
            } 
        }
    url = 'https://api.moltin.com/v2/customers'

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def get_customer(client_id, client_secret, customer_id):
    access_token = _get_access_token(client_id=client_id, client_secret=client_secret)

    headers = {
        'Authorization': access_token,
    }

    response = requests.get(f'https://api.moltin.com/v2/customers/{customer_id}', headers=headers)
    response.raise_for_status()

    print(response.json())