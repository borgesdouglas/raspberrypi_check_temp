#!/usr/bin/env python3
import subprocess
import re
import time
import requests
import os

## Configurações Pushover (substitua pelos seus)
USER_KEY = ''  # user 
API_TOKEN = '' # app 
URL = 'https://api.pushover.net/1/messages.json'

# Limites
TEMP_LIMITE = 55.0
INTERVALO_VERIFICACAO = 600  # segundos
COOLDOWN_MIN = 300  # 5 min entre notificações

ultima_notificacao = 0

def get_temperatura():
    """Obtém temperatura via vcgencmd (GPU/SoC). Retorna float em °C ou None se erro."""
    try:
        resultado = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True, check=True)
        match = re.search(r'temp=([\d.]+)', resultado.stdout)
        if match:
            return float(match.group(1))
    except (subprocess.CalledProcessError, ValueError):
        pass
    return None  # Fallback se falhar

def enviar_notificacao(temp):
    """Envia notificação via Pushover."""
    dados = {
        'token': API_TOKEN,
        'user': USER_KEY,
        'title': '🚨 Temperatura Alta no Raspberry Pi!',
        'message': f'A temperatura atingiu {temp:.1f}°C (limite: {TEMP_LIMITE}°C)',
        'priority': 2,  # Emergência (requer confirmação)
        'retry': 30,
        'expire': 300,
        'sound': 'siren'
    }
    try:
        resposta = requests.post(URL, data=dados)
        return resposta.json().get('status') == 1
    except Exception:
        return False

# Loop principal
print("Monitorando temperatura... (Ctrl+C para parar)")
while True:
    temp = get_temperatura()
    if temp is None:
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Erro ao ler temperatura")
    elif temp > TEMP_LIMITE:
        agora = time.time()
        if agora - ultima_notificacao > COOLDOWN_MIN:
            if enviar_notificacao(temp):
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Notificação enviada! Temp: {temp:.1f}°C")
                ultima_notificacao = agora
            else:
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Falha ao enviar notificação")
        else:
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Temp alta ({temp:.1f}°C), mas em cooldown")
    else:
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Temp OK: {temp:.1f}°C")
    
    time.sleep(INTERVALO_VERIFICACAO)

