from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_ID = int(os.getenv("MANAGER_ID"))

ADMIN_IDS = [5004870921, 5139970065, 1949773917]

user_data = {}
user_step = {}

questions = [
    ("name", "Nhập họ tên:"),
    ("position", "Nhập chức vụ:"),
    ("date", "Ngày nghỉ (vd: 02/05 đến 03/05):"),
    ("time", "Thời gian (vd: 13h-17h hoặc Cả ngày):"),
    ("reason", "Lý do:"),
    ("handover_person", "Người bàn giao (không có ghi: Không):"),
    ("handover_work", "Công việc bàn giao (không có ghi: Không):"),
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id] = {}
    user_step[user_id] = 0
    await update.message.reply_text("📌 Bắt đầu đơn xin nghỉ\n" + questions[0][1])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_step:
        await update.message.reply_text("Gõ /start để bắt đầu")
        return

    if user_step[user_id] >= len(questions):
        await update.message.reply_text("Đơn đã gửi rồi. Gõ /start để tạo đơn mới.")
        return

    key, _ = questions[user_step[user_id]]
    user_data[user_id][key] = text
    user_step[user_id] += 1

    if user_step[user_id] < len(questions):
        await update.message.reply_text(questions[user_step[user_id]][1])
    else:
        data = user_data[user_id]

        msg = f"""📌 ĐƠN XIN NGHỈ

👤 {data['name']}
💼 {data['position']}
📅 {data['date']}
⏰ {data['time']}
📝 {data['reason']}
📌 Bàn giao: {data['handover_person']} - {data['handover_work']}
"""

        keyboard = [[
            InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Từ chối", callback_data=f"reject_{user_id}")
        ]]

        await context.bot.send_message(
            chat_id=MANAGER_ID,
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("✅ Đã gửi quản lý")

        user_step.pop(user_id, None)
        user_data.pop(user_id, None)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.message.reply_text(
            f"⚠️ Bạn không có quyền duyệt\nID của bạn là: {query.from_user.id}"
        )
        return

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "approve":
        await context.bot.send_message(uid, "✅ Đơn đã được duyệt")
        await query.edit_message_text(query.message.text + f"\n\n✅ Đã duyệt bởi ID: {query.from_user.id}")
    else:
        await context.bot.send_message(uid, "❌ Đơn bị từ chối")
        await query.edit_message_text(query.message.text + f"\n\n❌ Đã từ chối bởi ID: {query.from_user.id}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

app.run_polling()