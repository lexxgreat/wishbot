import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import openai

TELEGRAM_TOKEN = "7638202633:AAFak_cCPHklvknTq1gmMDZ9A3LmQmRwBwM"
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

users_goals = {}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для исполнения твоих желаний. Используй /новоежелание чтобы начать!")

async def new_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ваше желание:")
    return 1

async def save_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    goal_text = update.message.text
    users_goals[user_id] = {
        "goal": goal_text,
        "steps": [],
        "done": []
    }
    await update.message.reply_text(f"Желание сохранено: {goal_text}. Добавь шаги с помощью /добавитьшаг")
    return ConversationHandler.END

async def add_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите шаг:")
    return 2

async def save_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    step_text = update.message.text
    if user_id in users_goals:
        users_goals[user_id]["steps"].append(step_text)
        await update.message.reply_text(f"Шаг добавлен: {step_text}")
    else:
        await update.message.reply_text("Сначала добавьте желание с помощью /новоежелание")
    return ConversationHandler.END

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = users_goals.get(user_id)
    if not data:
        await update.message.reply_text("У вас пока нет желаний. Добавьте с /новоежелание")
        return
    total = len(data["steps"])
    done = len(data["done"])
    await update.message.reply_text(f"Прогресс: {done}/{total} шагов выполнено.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_goal = users_goals.get(user_id, {}).get("goal", "желание не найдено")
    user_msg = update.message.text

    prompt = f"Пользователь работает над желанием: '{user_goal}'.\nВопрос пользователя: {user_msg}\nДай ответ с мотивацией или конкретным шагом, если возможно."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message["content"]
    await update.message.reply_text(answer)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

conv_goal = ConversationHandler(
    entry_points=[CommandHandler("новоежелание", new_goal)],
    states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_goal)]},
    fallbacks=[]
)

conv_step = ConversationHandler(
    entry_points=[CommandHandler("добавитьшаг", add_step)],
    states={2: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_step)]},
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_goal)
app.add_handler(conv_step)
app.add_handler(CommandHandler("прогресс", progress))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

app.run_polling()
