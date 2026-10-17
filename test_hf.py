"""Prueba del token de HuggingFace con el modelo BAAI/bge-m3.
Ejecutar:  python test_hf.py   (pide el token por teclado; no queda guardado)
"""
import getpass

import requests

token = getpass.getpass("Token de HuggingFace (no se muestra al escribir): ").strip()
url = "https://router.huggingface.co/hf-inference/models/BAAI/bge-m3/pipeline/feature-extraction"
headers = {"Authorization": f"Bearer {token}"}

pruebas = {
    "A) simple (un texto)": {"inputs": "prueba de embeddings"},
    "B) como lo envia Langflow (lista + options)": {
        "inputs": ["prueba uno", "prueba dos"],
        "options": {"wait_for_model": True, "use_cache": True},
    },
}


def forma(d):
    if isinstance(d, list):
        if d and isinstance(d[0], list):
            return f"{len(d)} vectores de {len(d[0])} valores"
        return f"1 vector de {len(d)} valores"
    return str(d)[:300]


for nombre, cuerpo in pruebas.items():
    try:
        r = requests.post(url, headers=headers, json=cuerpo, timeout=120)
        try:
            d = r.json()
        except Exception:
            d = r.text
        print(f"{nombre} | HTTP {r.status_code} | {forma(d)}")
    except Exception as e:
        print(f"{nombre} | ERROR de conexion: {e}")