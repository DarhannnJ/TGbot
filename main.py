from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
from bot.handlers import (
    start, history, total_sum, reliability,
    pdf_upload, start_credit, credit_amount,
    credit_term, cancel, CREDIT_AMOUNT, CREDIT_TERM
)
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    application = ApplicationBuilder() \
        .token("7766273088:AAGdOLkSGjASmAsyYQ77iG4e0DI5GSESuZ4") \
        .build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(MessageHandler(
        filters.Document.PDF,
        pdf_upload
    ))
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^Подать заявку$'), start_credit)],
        states={
            CREDIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, credit_amount)],
            CREDIT_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, credit_term)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(conv_handler)
    
    application.add_handler(MessageHandler(filters.Regex(r'^История переводов$'), history))
    application.add_handler(MessageHandler(filters.Regex(r'^Общая сумма$'), total_sum))
    application.add_handler(MessageHandler(filters.Regex(r'^Проверка надёжности$'), reliability))

    application.run_polling()

if __name__ == "__main__":
    main()