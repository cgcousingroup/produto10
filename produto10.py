import io
import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, JobQueue

def crc16(payload: str) -> str:
    polinomio = 0x1021
    resultado = 0xFFFF
    for char in payload:
        resultado ^= ord(char) << 8
        for _ in range(8):
            if resultado & 0x8000:
                resultado = (resultado << 1) ^ polinomio
            else:
                resultado <<= 1
            resultado &= 0xFFFF
    return f"{resultado:04X}"

def monta_campo(id: str, valor: str) -> str:
    tamanho = f"{len(valor):02}"
    return f"{id}{tamanho}{valor}"

def gerar_pix(chave, nome, cidade, valor=None, descricao=None):
    payload = ''
    payload += monta_campo('00', '01')
    payload += monta_campo('01', '12')
    gui = monta_campo('00', 'BR.GOV.BCB.PIX')
    chave_pix = monta_campo('01', chave)
    descricao_campo = monta_campo('02', descricao) if descricao else ''
    merchant_account = monta_campo('26', gui + chave_pix + descricao_campo)
    payload += merchant_account
    payload += monta_campo('52', '0000')
    payload += monta_campo('53', '986')
    if valor:
        payload += monta_campo('54', f"{valor:.2f}")
    payload += monta_campo('58', 'BR')
    payload += monta_campo('59', nome[:25])
    payload += monta_campo('60', cidade[:15])
    txid = monta_campo('05', '***')
    payload += monta_campo('62', txid)
    payload_sem_crc = payload + '6304'
    crc = crc16(payload_sem_crc)
    payload_completo = payload_sem_crc + crc
    return payload_completo

def gerar_qrcode_pix(chave, nome, cidade, valor=None, descricao=None):
    payload = gerar_pix(chave, nome, cidade, valor, descricao)
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio, payload

TOKEN = '7672360069:AAFrSEEMHYRofNnyWR3jYiCbqPwyJR-LY04'
SUPORTE_USERNAME = '@supvipoficial'
CHAVE_PIX = '5a5dc31f-f8a0-4711-9268-ba923769b518'
NOME = 'CGCOUSIN'
CIDADE = 'SAO PAULO'
DESCRICAO = 'CLUBEDO1'
VALOR_NORMAL = 1.00
VALOR_PROMO = 5.00
DESCRICAO_PROMO = 'VIPCLUBE1'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio, payload = gerar_qrcode_pix(CHAVE_PIX, NOME, CIDADE, valor=VALOR_NORMAL, descricao=DESCRICAO)
    await update.message.reply_photo(photo=bio, caption="Escaneie o QRCode para pagar VIP R$ 1,00. Depois envie o comprovante para: @supvipoficial")
    await update.message.reply_text(f"Código Pix para copiar:\n\n`{payload}`", parse_mode='MarkdownV2')

    # Agendar a oferta com vídeo e botão após 5 minutos (300 segundos)
    context.job_queue.run_once(enviar_oferta, 300, chat_id=update.effective_chat.id)

async def enviar_oferta(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    bot = context.bot

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 QUERO a oferta!", callback_data='quero_oferta')]
    ])

    legenda = (
        "Ainda não se tornou VIP? 😳\n\n"
        "Por você ainda não ter se tornado VIP, lançamos o VIP de entrada...\n\n"
        "😈 Novinhas, Amador e Incesto tudo por R$5,00\n\n"
        "Tem medo? Acha caro? Dúvidas? Acabou o problema, com R$5,00 o risco é menor, e o tesão é garantido!"
    )

    with open("oferta.mp4", 'rb') as video_file:
        await bot.send_video(chat_id=chat_id, video=video_file, caption=legenda, reply_markup=keyboard)

async def aceitar_oferta_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    bio, payload = gerar_qrcode_pix(CHAVE_PIX, NOME, CIDADE, valor=VALOR_PROMO, descricao=DESCRICAO_PROMO)
    
    await query.message.reply_photo(photo=bio, caption="✅ Oferta ativada! Pague VIP Proibidão R$ 5,00. Depois envie o comprovante para: @supvipoficial")
    await query.message.reply_text(f"Código Pix para copiar:\n\n`{payload}`", parse_mode='MarkdownV2')

async def receber_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suporte_chat = await context.bot.get_chat(SUPORTE_USERNAME)
    for photo in update.message.photo:
        await context.bot.forward_message(chat_id=supporte_chat.id,
                                          from_chat_id=update.message.chat_id,
                                          message_id=update.message.message_id)
        break
    await update.message.reply_text("Comprovante enviado ao suporte. Obrigado!")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO & (~filters.COMMAND), receber_comprovante))
    app.add_handler(CallbackQueryHandler(aceitar_oferta_callback, pattern='^quero_oferta$'))

    print("Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
