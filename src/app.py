# -*- coding: utf-8 -*-

import streamlit as st
import requests
import pycountry
import os
from dotenv import load_dotenv
from babel import Locale

# Carrega as variáveis do arquivo .env
load_dotenv()

# Recupera a subscription key da variável de ambiente
SUBSCRIPTION_KEY = os.getenv("SUBSCRIPTION_KEY")
if not SUBSCRIPTION_KEY:
    st.error("A Subscription Key não foi encontrada. Verifique se o arquivo .env está configurado corretamente.")

API_URL = "https://data.trade.gov/de_minimis/v1/search"

st.title("Consulta De Minimis")

# Entrada do usuário: nome ou código ISO do país
user_input = st.text_input("Digite o nome ou código ISO do país:")

def get_iso_code(user_input):
    """
    Converte a entrada do usuário para o código ISO de 2 letras.
    Se a entrada tiver 2 caracteres, assume que já é o código.
    Primeiro, tenta com pycountry (que usa nomes em inglês).
    Se não encontrar, utiliza Babel para tentar localizar o país em inglês, espanhol ou português.
    """
    user_input = user_input.strip()
    if len(user_input) == 2:
        return user_input.upper()
    # Primeiro, tenta o pycountry
    try:
        country = pycountry.countries.lookup(user_input)
        return country.alpha_2
    except LookupError:
        pass

    # Fallback: usa Babel para verificar nomes em diferentes idiomas
    locales = ['en', 'es', 'pt']
    for loc in locales:
        locale_data = Locale(loc)
        for iso_code, country_name in locale_data.territories.items():
            # Ignora chaves que não são letras (por exemplo, '001' para "World")
            if not iso_code.isalpha():
                continue
            if country_name.lower() == user_input.lower():
                return iso_code
    # Se não encontrar uma correspondência exata, tenta uma busca parcial
    for loc in locales:
        locale_data = Locale(loc)
        for iso_code, country_name in locale_data.territories.items():
            if not iso_code.isalpha():
                continue
            if user_input.lower() in country_name.lower():
                return iso_code
    return None

if st.button("Buscar"):
    iso_code = get_iso_code(user_input)
    
    if not iso_code:
        st.warning("Não foi possível determinar o código ISO a partir da entrada. Tente novamente.")
    else:
        params = {"country_codes": iso_code, "size": 1}
        headers = {
            "Cache-Control": "no-cache",
            "subscription-key": SUBSCRIPTION_KEY
        }
        
        response = requests.get(API_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                country_data = results[0]
                st.subheader(f"{country_data['country_name']} ({country_data['country_code']})")
                st.write(f"**De Minimis:** {country_data['de_minimis_value']} {country_data['de_minimis_currency']}")
                
                vat_amount = country_data.get("vat_amount")
                vat_currency = country_data.get("vat_currency")
                if vat_amount is not None:
                    st.write(f"**VAT Amount:** {vat_amount} {vat_currency if vat_currency else ''}")
                
                comment = country_data.get("comment")
                if comment:
                    st.write(f"**Comentário:** {comment}")
            else:
                st.write("Nenhum resultado encontrado para o país informado.")
        else:
            st.error(f"Erro {response.status_code}: {response.text}")

