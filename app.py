
import asyncio
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIG ===
BOT_TOKEN = "8164513264:AAHOUXvrTvSWW7kg_bHzizUArMxl73RI9aM"
CHAT_ID = 845872864
TOKEN_INTERESSE = ["bitcoin", "ethereum", "solana"]
PALAVRAS_CHAVE = ["trump", "donald", "elon", "musk", "barron"]

# === ALERTA VIA TELEGRAM ===
async def send_telegram_alert(mensagem: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem}
    requests.post(url, data=payload)

# === COMANDO DE SIMULAÇÃO ===
async def simular_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == CHAT_ID:
        await update.message.reply_text("🚨 Alerta TESTE: Bitcoin caiu 5%\n💰 Preço atual: R$ 250.000,00")
    else:
        await update.message.reply_text("❌ Acesso negado.")

# === MONITORAMENTO DE PREÇOS ===
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

async def monitorar():
    while True:
        for token_id in TOKEN_INTERESSE:
            preco_atual = consultar_preco_brl(token_id)
            if preco_atual is None:
                continue
            preco_antigo = precos_referencia.get(token_id)
            if preco_antigo:
                variacao = ((preco_atual - preco_antigo) / preco_antigo) * 100
                if variacao <= -1:
                    msg = f"🔻 {token_id.upper()} caiu {abs(variacao):.2f}%\n💰 Preço atual: {formatar_brl(preco_atual)}"
                    await send_telegram_alert(msg)
                elif variacao >= 5:
                    msg = f"🚀 {token_id.upper()} subiu {variacao:.2f}%\n💰 Preço atual: {formatar_brl(preco_atual)}"
                    await send_telegram_alert(msg)
            precos_referencia[token_id] = preco_atual
        await asyncio.sleep(60)

# === EXECUÇÃO PRINCIPAL ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("simular_alerta", simular_alerta))

    # Executa monitoramento e bot simultaneamente
    await asyncio.gather(
        app.run_polling(),
        monitorar()
    )

if __name__ == "__main__":
    asyncio.run(main())
