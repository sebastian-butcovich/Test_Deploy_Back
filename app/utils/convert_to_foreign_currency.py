import requests


def convert_to_foreign_currency(value_pesos: float, currency: str = "usd", type_of_currency: str = "oficial"):
    if currency == "usd".casefold():
        response = requests.get(f"https://dolarapi.com/v1/dolares/{type_of_currency}")
    else:
        response = requests.get(f"https://dolarapi.com/v1/cotizaciones/{currency}")
    if response.status_code == 200:
        currency_venta = response.json().get("venta", 1.0)
        return value_pesos / currency_venta
    else:
        raise Exception(f"Error en llamada a API de cotizaciones. Status_code: {response.status_code}, Reason: {response.reason}, text: {response.text}")


def convert_list_to_foreign_currency(contents: list, currency: str = "usd", type_of_currency: str = "oficial"):
    if currency == "usd".casefold():
        response = requests.get(f"https://dolarapi.com/v1/dolares/{type_of_currency}")
    else:
        response = requests.get(f"https://dolarapi.com/v1/cotizaciones/{currency}")
    if response.status_code == 200:
        currency_venta = response.json().get("venta", 1.0)
        for content in contents:
            content.monto = content.monto / currency_venta
        return contents
    else:
        raise Exception(f"Error en llamada a API de cotizaciones. Status_code: {response.status_code}, Reason: {response.reason}, text: {response.text}")

# Documentacion microservicio externo: https://dolarapi.com/docs/argentina/
