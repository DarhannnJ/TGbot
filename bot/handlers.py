import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db.database import DB
from utils.pdf_parser import parse_pdf
from utils.fraud_check import calculate_reliability

db = DB()
CREDIT_AMOUNT, CREDIT_TERM = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["История переводов", "Общая сумма"],
        ["Проверка надёжности", "Подать заявку"]
    ]
    await update.message.reply_text(
        "🔐 Бот для проверки переводов от *Дархана*\nВыберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transactions = db.get_transactions(user_id)
    response = "📜 *История переводов:*\n" + "\n".join(
        [f"• {t['date']} - {t['amount']} KGS ({t['recipient']})" 
         for t in transactions]
    ) if transactions else "История пуста."
    await update.message.reply_text(response, parse_mode="Markdown")

async def total_sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    total = db.get_total_sum(user_id)
    await update.message.reply_text(f"💰 *Общая сумма:* {total:.2f} KGS", parse_mode="Markdown")

async def reliability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transactions = db.get_transactions(user_id)
    rating = calculate_reliability(transactions)
    await update.message.reply_text(
        f"🛡️ *Рейтинг надёжности:* {rating}%\n"
        "Критерии:\n- Чек от Дархана ✔️\n- Сумма > 0 ✔️\n- Дата в пределах месяца ✔️",
        parse_mode="Markdown"
    )

async def pdf_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = await update.message.document.get_file()
    file_path = f"temp_{user_id}.pdf"
    
    try:
        await file.download_to_drive(file_path)
        parsed_data = parse_pdf(file_path)
        
        if not parsed_data:
            await update.message.reply_text("❌ Неверный формат чека!")
            return
        
        if "дархан" not in parsed_data["recipient"].lower():
            await update.message.reply_text("🚫 Только чеки от Дархана!")
            return
        
        if db.is_duplicate(parsed_data["serial"], parsed_data["serial"]):
            await update.message.reply_text("⚠️ Чек уже обработан!")
            return
        
        db.add_transfer(
            user_id,
            parsed_data["serial"],
            parsed_data["serial"],
            parsed_data["amount"],
            parsed_data["recipient"],
            parsed_data["date"]
        )
        await update.message.reply_text("✅ Чек успешно добавлен!")
    
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def start_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите сумму кредита:")
    return CREDIT_AMOUNT

async def credit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        context.user_data["credit_amount"] = amount
        await update.message.reply_text("Введите срок (в месяцах):")
        return CREDIT_TERM
    except:
        await update.message.reply_text("❌ Неверный формат суммы!")
        return CREDIT_AMOUNT

async def credit_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        term = int(update.message.text)
        db.save_credit_application(
            update.effective_user.id,
            context.user_data["credit_amount"],
            term
        )
        await update.message.reply_text("✅ Заявка отправлена!")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Неверный срок!")
        return CREDIT_TERM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END