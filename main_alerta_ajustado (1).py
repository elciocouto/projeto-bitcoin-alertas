import requests
import time
from alert import send_telegram_alert

TOKEN_INTERESSE = ["bitcoin", "ethereum", "solana"]
PALAVRAS_CHAVE = ["trump", "donald", "elon", "musk", "barron"]
precos_referencia = {}
tokens_ja_alertados = set()
novos_tokens_detectados = set()

def consultar_preco_brl(token_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=brl"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()[token_id]["brl"]
    return None

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def detectar_tokens_estrategicos_novos():
    global novos_tokens_detectados
    url = "https://api.coingecko.com/api/v3/coins/list"
    r = requests.get(url)
    mensagens = []

    if r.status_code == 200:
        tokens = r.json()
        for token in tokens:
            nome = token["name"].lower()
            simbolo = token["symbol"].lower()
            if any(chave in nome or chave in simbolo for chave in PALAVRAS_CHAVE):
                identificador = f"{token['id']}::{nome}"
                if identificador not in novos_tokens_detectados:
                    link = f"https://www.coingecko.com/en/coins/{token['id']}"
                    mensagens.append(f"🆕 Novo token detectado: {token['name']} ({token['symbol']})\n🔗 {link}")
                    novos_tokens_detectados.add(identificador)
    return mensagens

def monitorar():
    intervalo_verificacao = 60  # segundos
    cooldown = 600  # 10 minutos
    ultimo_alerta = {}

    for token in TOKEN_INTERESSE:
        preco = consultar_preco_brl(token)
        if preco:
            precos_referencia[token] = preco
            ultimo_alerta[token] = 0

    while True:
        mensagens = []

        for token in TOKEN_INTERESSE:
            preco_atual = consultar_preco_brl(token)
            preco_base = precos_referencia.get(token)
            agora = time.time()

            if preco_atual and preco_base:
                variacao = ((preco_atual - preco_base) / preco_base) * 100

                if agora - ultimo_alerta[token] >= cooldown:
                    preco_formatado = formatar_brl(preco_atual)

                    if variacao >= 5:
                        mensagens.append(
                            f"🚀 {token.upper()} subiu {variacao:.2f}%.\n💰 Valor atual: {preco_formatado}"
                        )
                        precos_referencia[token] = preco_atual
                        ultimo_alerta[token] = agora

                    elif variacao <= -1:  # ⚠️ Alterado aqui
                        mensagens.append(
                            f"📉 {token.upper()} caiu {variacao:.2f}%.\n💰 Valor atual: {preco_formatado}"
                        )
                        precos_referencia[token] = preco_atual
                        ultimo_alerta[token] = agora

        mensagens += detectar_tokens_estrategicos_novos()

        if mensagens:
            alerta = "\n\n".join(mensagens)
            send_telegram_alert(alerta)

        time.sleep(intervalo_verificacao)

if __name__ == "__main__":
    monitorar()

