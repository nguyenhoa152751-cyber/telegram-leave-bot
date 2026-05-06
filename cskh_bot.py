from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = "8288971738:AAEZR5XUzsdhQaHAPCN7P45v3NAdbmR_-Nc"

ADMIN_GROUP_ID = -1003967360441
ADMIN_IDS = [6785796450, 5004870921, 5139970065, 1949773917]

BC88_LINK = "https://bc88bet.com"

user_data = {}
ticket_map = {}

MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("💰 Nạp / Rút tiền", callback_data="nap_rut")],
    [InlineKeyboardButton("🎁 Khuyến mãi", callback_data="khuyen_mai")],
    [InlineKeyboardButton("⚠️ Lỗi tài khoản / Lỗi game", callback_data="loi")],
    [InlineKeyboardButton("📞 Gặp CSKH", callback_data="cskh")],
    [
        InlineKeyboardButton("📝 Đăng ký", url=BC88_LINK),
        InlineKeyboardButton("🔐 Đăng nhập", url=BC88_LINK)
    ]
])

def admin_buttons(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ DUYỆT", callback_data=f"approve:{user_id}"),
            InlineKeyboardButton("❌ TỪ CHỐI", callback_data=f"reject:{user_id}")
        ],
        [InlineKeyboardButton("🌐 Link BC88", url=BC88_LINK)]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Chào mừng quý khách đến với CSKH BC88BET\n\n"
        "Quý khách vui lòng chọn mục cần hỗ trợ:",
        reply_markup=MAIN_MENU
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ID nhóm/chat hiện tại: `{update.effective_chat.id}`",
        parse_mode="Markdown"
    )

async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    titles = {
        "nap_rut": "💰 Nạp / Rút tiền",
        "khuyen_mai": "🎁 Khuyến mãi",
        "loi": "⚠️ Lỗi tài khoản / Lỗi game",
        "cskh": "📞 Gặp CSKH"
    }

    user_id = query.from_user.id

    user_data[user_id] = {
        "step": "username",
        "category": titles.get(query.data, "CSKH"),
        "photos": [],
        "documents": [],
        "videos": []
    }

    await query.message.reply_text("👉 Vui lòng nhập TÊN TÀI KHOẢN:")

async def handle_private_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data:
        await update.message.reply_text(
            "Vui lòng chọn mục cần hỗ trợ:",
            reply_markup=MAIN_MENU
        )
        return

    data = user_data[user_id]

    if data["step"] == "username":
        data["username"] = text
        data["step"] = "phone"
        await update.message.reply_text("👉 Vui lòng nhập SỐ ĐIỆN THOẠI:")
        return

    if data["step"] == "phone":
        data["phone"] = text
        data["step"] = "content"
        await update.message.reply_text("👉 Vui lòng nhập nội dung hoặc gửi hình ảnh cần hỗ trợ:")
        return

    if data["step"] == "content":
        data["content"] = text
        await send_ticket_to_admin(update, context, user_id)

async def handle_private_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo_id = update.message.photo[-1].file_id
    caption = update.message.caption or "Khách gửi hình ảnh."

    name = update.message.from_user.full_name
    username = update.message.from_user.username
    telegram_user = f"@{username}" if username else "Không có username"

    if user_id in user_data:
        data = user_data[user_id]
        if data.get("step") == "content":
            data["content"] = caption
            data.setdefault("photos", []).append(photo_id)
            await send_ticket_to_admin(update, context, user_id)
            return

    msg = (
        "📷 KHÁCH GỬI HÌNH ẢNH BỔ SUNG\n\n"
        f"👤 Khách: {name}\n"
        f"🔗 Telegram: {telegram_user}\n"
        f"🆔 ID khách: {user_id}\n"
        f"📝 Ghi chú: {caption}"
    )

    sent = await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=photo_id,
        caption=msg
    )

    ticket_map[sent.message_id] = user_id
    await update.message.reply_text("✅ CSKH đã nhận hình ảnh của quý khách.")

async def handle_private_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    document_id = update.message.document.file_id
    caption = update.message.caption or "Khách gửi file bổ sung."

    sent = await context.bot.send_document(
        chat_id=ADMIN_GROUP_ID,
        document=document_id,
        caption=f"📎 KHÁCH GỬI FILE\n🆔 ID khách: {user_id}\n📝 {caption}"
    )

    ticket_map[sent.message_id] = user_id
    await update.message.reply_text("✅ CSKH đã nhận file của quý khách.")

async def handle_private_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    video_id = update.message.video.file_id
    caption = update.message.caption or "Khách gửi video bổ sung."

    sent = await context.bot.send_video(
        chat_id=ADMIN_GROUP_ID,
        video=video_id,
        caption=f"🎥 KHÁCH GỬI VIDEO\n🆔 ID khách: {user_id}\n📝 {caption}"
    )

    ticket_map[sent.message_id] = user_id
    await update.message.reply_text("✅ CSKH đã nhận video của quý khách.")

async def send_ticket_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    data = user_data[user_id]

    name = update.message.from_user.full_name
    username = update.message.from_user.username
    telegram_user = f"@{username}" if username else "Không có username"

    msg = (
        "📩 YÊU CẦU CSKH MỚI\n\n"
        f"👤 Khách: {name}\n"
        f"🔗 Telegram: {telegram_user}\n"
        f"🆔 ID khách: {user_id}\n"
        f"📌 Hạng mục: {data.get('category')}\n"
        f"🎮 Tài khoản: {data.get('username')}\n"
        f"📞 SĐT: {data.get('phone')}\n"
        f"📝 Nội dung: {data.get('content')}\n\n"
        "👉 Admin bấm DUYỆT / TỪ CHỐI.\n"
        "👉 Muốn trả lời khách: Reply trực tiếp tin nhắn này trong nhóm."
    )

    sent = await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=msg,
        reply_markup=admin_buttons(user_id)
    )

    ticket_map[sent.message_id] = user_id

    for photo_id in data.get("photos", []):
        photo_msg = await context.bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=photo_id,
            caption=f"📷 Ảnh khách gửi\n🆔 ID khách: {user_id}"
        )
        ticket_map[photo_msg.message_id] = user_id

    await update.message.reply_text(
        "✅ CSKH đã tiếp nhận yêu cầu của quý khách.\n"
        "Bộ phận hỗ trợ sẽ phản hồi trong thời gian sớm nhất ạ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Đăng ký / Đăng nhập BC88", url=BC88_LINK)]
        ])
    )

    if user_id in user_data:
        del user_data[user_id]

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = query.from_user.id

    if admin_id not in ADMIN_IDS:
        await query.answer("Bạn không có quyền xử lý yêu cầu này.", show_alert=True)
        return

    action, customer_id = query.data.split(":")
    customer_id = int(customer_id)

    if action == "approve":
        await context.bot.send_message(
            chat_id=customer_id,
            text="✅ Yêu cầu của quý khách đã được CSKH tiếp nhận và duyệt xử lý.\nNhân viên sẽ phản hồi sớm ạ."
        )
        await query.answer("Đã duyệt yêu cầu.")
        await query.message.reply_text(f"✅ Admin {query.from_user.full_name} đã DUYỆT yêu cầu.")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=customer_id,
            text="❌ Yêu cầu của quý khách hiện chưa đủ thông tin để xử lý.\nVui lòng gửi lại đầy đủ tài khoản, SĐT và nội dung cần hỗ trợ ạ."
        )
        await query.answer("Đã từ chối yêu cầu.")
        await query.message.reply_text(f"❌ Admin {query.from_user.full_name} đã TỪ CHỐI yêu cầu.")

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    if update.message.from_user.id not in ADMIN_IDS:
        return

    if not update.message.reply_to_message:
        return

    original_id = update.message.reply_to_message.message_id
    customer_id = ticket_map.get(original_id)

    if not customer_id:
        return

    if update.message.text:
        await context.bot.send_message(
            chat_id=customer_id,
            text=f"📩 CSKH BC88BET phản hồi:\n\n{update.message.text}"
        )

    if update.message.photo:
        await context.bot.send_photo(
            chat_id=customer_id,
            photo=update.message.photo[-1].file_id,
            caption=update.message.caption or "📩 CSKH BC88BET gửi hình ảnh phản hồi."
        )

    if update.message.document:
        await context.bot.send_document(
            chat_id=customer_id,
            document=update.message.document.file_id,
            caption=update.message.caption or "📎 CSKH BC88BET gửi file phản hồi."
        )

    if update.message.video:
        await context.bot.send_video(
            chat_id=customer_id,
            video=update.message.video.file_id,
            caption=update.message.caption or "🎥 CSKH BC88BET gửi video phản hồi."
        )

    if customer_id in user_data:
        del user_data[customer_id]

    await update.message.reply_text("✅ Đã gửi phản hồi tới khách hàng.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))

    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(approve|reject):"))
    app.add_handler(CallbackQueryHandler(menu_click))

    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_private_text))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.PHOTO, handle_private_photo))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Document.ALL, handle_private_document))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.VIDEO, handle_private_video))

    app.add_handler(MessageHandler(filters.ChatType.GROUPS & (filters.TEXT | filters.PHOTO | filters.Document.ALL | filters.VIDEO), admin_reply))

    print("Bot CSKH PRO đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()