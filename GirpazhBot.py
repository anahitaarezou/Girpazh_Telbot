from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)
import csv
from datetime import datetime
import os
import logging

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# مراحل فرم - تغییر ترتیب (اول مدل، بعد سال، بعد قطعه، آخر شاسی)
ASK_MODEL, ASK_YEAR, ASK_PART, ASK_CHASSIS = range(4)

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
                    'Part',
                    'Chassis',
                    'Timestamp'
                ])
            writer.writerow([
                user_id,
                username,
                user_data.get('model', ''),
                user_data.get('year', ''),
                user_data.get('part', ''),
                user_data.get('chassis', ''),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")

# دکمه‌های اینلاین برای بازگشت (جایگزین دکمه کیبورد)
def get_navigation_markup(current_step):
    keyboard = []
    
    # دکمه بازگشت به مرحله قبل فقط از مرحله دوم به بعد نشان داده شود
    if current_step > ASK_MODEL:
        keyboard.append([InlineKeyboardButton("⬅️ بازگشت به مرحله قبل", callback_data="prev_step")])
    
    # دکمه بازگشت به منوی اصلی همیشه نشان داده شود
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

# تابع شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # پاک کردن داده‌های قبلی
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
        await update.callback_query.message.edit_text(welcome_message, reply_markup=reply_markup)

# مرحله ۱: مدل خودرو
async def ask_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Current step: {context.user_data.get('current_step')}")
    # مقداردهی اولیه رحله جاری
    context.user_data["current_step"] = ASK_MODEL
    
    query = update.callback_query
    if query:
        await query.answer()
    
    message_text = "مرحله ۱: مدل خودرو را وارد کنید:"
    reply_markup = get_navigation_markup(ASK_MODEL)
    
    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif query:
        await query.edit_message_text(message_text, reply_markup=reply_markup)
    
    return ASK_MODEL

# مرحله ۲: سال ساخت
async def ask_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        # اجازه می‌دهیم button_handler پردازش کند
        return ASK_MODEL

    if update.message and update.message.text:
        context.user_data["model"] = update.message.text.strip()
        context.user_data["current_step"] = ASK_YEAR
        
        await update.message.reply_text(
            "مرحله ۲: سال ساخت خودرو را وارد کنید:",
            reply_markup=get_navigation_markup(ASK_YEAR)
        )
        return ASK_YEAR
    else:
        await update.message.reply_text(
            "❗️لطفاً مدل خودرو را به صورت متنی وارد کنید.",
            reply_markup=get_navigation_markup(ASK_MODEL)
        )
        return ASK_MODEL

async def ask_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        # اجازه می‌دهیم button_handler پردازش کند
        return ASK_YEAR

    if update.message and update.message.text:
        context.user_data["year"] = update.message.text.strip()
        context.user_data["current_step"] = ASK_PART
        
        await update.message.reply_text(
            "مرحله ۳: نام قطعه موردنظر را وارد کنید:",
            reply_markup=get_navigation_markup(ASK_PART)
        )
        return ASK_PART
    else:
        await update.message.reply_text(
            "❗️لطفاً سال ساخت را به صورت عددی وارد کنید.",
            reply_markup=get_navigation_markup(ASK_YEAR)
        )
        return ASK_YEAR

async def ask_chassis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        # اجازه می‌دهیم button_handler پردازش کند
        return ASK_PART

    if update.message and update.message.text:
        context.user_data["part"] = update.message.text.strip()
        context.user_data["current_step"] = ASK_CHASSIS
        
        await update.message.reply_text(
            "مرحله ۴: شماره شاسی خودرو را وارد کنید:",
            reply_markup=get_navigation_markup(ASK_CHASSIS)
        )
        return ASK_CHASSIS
    else:
        await update.message.reply_text(
            "❗️لطفاً نام قطعه را به صورت متنی وارد کنید.",
            reply_markup=get_navigation_markup(ASK_PART)
        )
        return ASK_PART
# ثبت نهایی اطلاعات
async def finalize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        # اجازه می‌دهیم button_handler پردازش کند
        return ASK_CHASSIS

    if update.message and update.message.text:
        user = update.effective_user
        context.user_data["chassis"] = update.message.text.strip()

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
            f"• قطعه: {context.user_data['part']}\n"
            f"• شماره شاسی: {context.user_data['chassis']}\n\n"
            "📞 همکاران ما به زودی با شما تماس خواهند گرفت."
        )

        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❗️لطفاً شماره شاسی را به صورت صحیح وارد کنید.",
            reply_markup=get_navigation_markup(ASK_CHASSIS)
        )
        return ASK_CHASSIS
# مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text(
            "📌 این ربات جهت ثبت سفارش قطعات خودروی شما طراحی شده است.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]])
        )
    elif query.data == "main_menu":
        await start(update, context)
        return ConversationHandler.END
    elif query.data == "start_form":
        return await ask_model(update, context)
    elif query.data == "show_phone":
        await query.edit_message_text(
            "☎ برای تماس با پشتیبانی:\n📱 0992 864 2905",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]])
        )
    elif query.data == "prev_step":
        current_step = context.user_data.get("current_step", ASK_MODEL)
        logging.info(f"Prev step requested, current_step: {current_step}")
        
        if current_step == ASK_YEAR:
            logging.info("Returning to ASK_MODEL")
            await query.edit_message_text(
                "مرحله ۱: مدل خودرو را وارد کنید:",
                reply_markup=get_navigation_markup(ASK_MODEL)
            )
            context.user_data["current_step"] = ASK_MODEL
            return ASK_MODEL
        elif current_step == ASK_PART:
            logging.info("Returning to ASK_YEAR")
            await query.edit_message_text(
                "مرحله ۲: سال ساخت خودرو را وارد کنید:",
                reply_markup=get_navigation_markup(ASK_YEAR)
            )
            context.user_data["current_step"] = ASK_YEAR
            return ASK_YEAR
        elif current_step == ASK_CHASSIS:
            logging.info("Returning to ASK_PART")
            await query.edit_message_text(
                "مرحله ۳: نام قطعه موردنظر را وارد کنید:",
                reply_markup=get_navigation_markup(ASK_PART)
            )
            context.user_data["current_step"] = ASK_PART
            return ASK_PART
        else:
            logging.info("No previous step, returning to main menu")
            await start(update, context)
            return ConversationHandler.END

# لغو گفتگو و بازگشت به منوی اصلی
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# اجرای برنامه
if __name__ == '__main__':
    app = ApplicationBuilder().token("7724167611:AAGYSWUpQK90jrF57DRk5mto32dn65GuosU").build()

    # تغییر در ترتیب حالت‌ها (ASK_PART و ASK_CHASSIS جابجا شدند)
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^start_form$")],
        states={
            ASK_MODEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_year),
                CallbackQueryHandler(button_handler)
            ],
            ASK_YEAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_part),
                CallbackQueryHandler(button_handler)
            ],
            ASK_PART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_chassis),
                CallbackQueryHandler(button_handler)
            ],
            ASK_CHASSIS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, finalize),
                CallbackQueryHandler(button_handler)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(button_handler, pattern="^main_menu$"),
            CommandHandler("cancel", cancel)
        ]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.info("✅ ربات آماده است...")
    app.run_polling()
