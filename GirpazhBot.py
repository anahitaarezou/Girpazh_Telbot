from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)
import csv
from datetime import datetime
import os
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# مراحل فرم
ASK_MODEL, ASK_YEAR, ASK_CHASSIS, ASK_PART = range(4)

DATA_FILE = "user_requests.csv"

def save_to_csv(user_data, user_id, username):
    file_exists = os.path.isfile(DATA_FILE)
    try:
        with open(DATA_FILE, mode='a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    'User ID',
                    'Username',
                    'Model',
                    'Year',
                    'Chassis',
                    'Part',
                    'Timestamp'
                ])
            writer.writerow([
                user_id,
                username,
                user_data.get('model', ''),
                user_data.get('year', ''),
                user_data.get('chassis', ''),
                user_data.get('part', ''),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")

# دکمه بازگشت به منوی اصلی
def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🔙 بازگشت به منوی اصلی")]],
        resize_keyboard=True
    )

# تابع شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name

    keyboard = [
        [InlineKeyboardButton("🚘 شروع ثبت اطلاعات خودرو", callback_data="start_form")],
        [InlineKeyboardButton("📱 شماره پشتیبانی: 09928642905", callback_data="show_phone")],
        [InlineKeyboardButton("ℹ درباره ما", callback_data="about")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = f"سلام {name} عزیز! 👋\nبه ربات پشتیبانی گیرپاژ خوش آمدید.\nلطفاً یکی از گزینه‌ها را انتخاب کن:"

    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_message, reply_markup=reply_markup)

# مرحله ۱: مدل خودرو
async def ask_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        if update.message.text == "🔙 بازگشت به منوی اصلی":
            await cancel(update, context)
            return ConversationHandler.END
        context.user_data["model"] = update.message.text.strip()
        await update.message.reply_text(
            "مرحله ۲️⃣: سال ساخت خودرو را وارد کنید:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_YEAR
    else:
        await update.message.reply_text(
            "❗️لطفاً مدل خودرو را به صورت متنی وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_MODEL

# مرحله ۲: سال ساخت
async def ask_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        if update.message.text == "🔙 بازگشت به منوی اصلی":
            await cancel(update, context)
            return ConversationHandler.END
        context.user_data["year"] = update.message.text.strip()
        await update.message.reply_text(
            "مرحله ۳️⃣: شماره شاسی خودرو را وارد کنید:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_CHASSIS
    else:
        await update.message.reply_text(
            "❗️لطفاً سال ساخت را به صورت عددی وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_YEAR

# مرحله ۳: شماره شاسی
async def ask_chassis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        if update.message.text == "🔙 بازگشت به منوی اصلی":
            await cancel(update, context)
            return ConversationHandler.END
        context.user_data["chassis"] = update.message.text.strip()
        await update.message.reply_text(
            "مرحله ۴️⃣: نام قطعه موردنظر را وارد کنید:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PART
    else:
        await update.message.reply_text(
            "❗️لطفاً شماره شاسی را به صورت صحیح وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_CHASSIS

# مرحله ۴: نام قطعه
async def ask_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        if update.message.text == "🔙 بازگشت به منوی اصلی":
            await cancel(update, context)
            return ConversationHandler.END
        user = update.effective_user
        context.user_data["part"] = update.message.text.strip()

        # ذخیره اطلاعات
        save_to_csv(
            user_data=context.user_data,
            user_id=user.id,
            username=user.username or user.first_name
        )

        response = (
            "✅ اطلاعات شما با موفقیت ثبت شد!\n\n"
            "📝 جزئیات ثبت شده:\n"
            f"• مدل: {context.user_data['model']}\n"
            f"• سال ساخت: {context.user_data['year']}\n"
            f"• شماره شاسی: {context.user_data['chassis']}\n"
            f"• قطعه: {context.user_data['part']}\n\n"
            "📞 همکاران ما به زودی با شما تماس خواهند گرفت."
        )

        await update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❗️لطفاً نام قطعه را به صورت متنی وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PART

# مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text("📌 این ربات جهت ثبت سفارش قطعات خودروی شما طراحی شده است.")
    elif query.data == "start_form":
        await query.edit_message_text("مرحله ۱️⃣: مدل خودرو را وارد کنید:")
        await update.effective_chat.send_message(
            "لطفاً مدل خودرو را وارد کنید:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_MODEL
    elif query.data == "show_phone":
        await query.edit_message_text("☎ برای تماس با پشتیبانی:\n📱 0992 864 2905")

# لغو گفتگو و بازگشت به منوی اصلی
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# اجرای برنامه
if __name__ == '__main__':
    app = ApplicationBuilder().token("7724167611:AAGYSWUpQK90jrF57DRk5mto32dn65GuosU").build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^start_form$")],
        states={
            ASK_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_model)],
            ASK_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_year)],
            ASK_CHASSIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_chassis)],
            ASK_PART: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_part)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 بازگشت به منوی اصلی$"), cancel),
                   CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.info("✅ ربات آماده است...")
    app.run_polling()
