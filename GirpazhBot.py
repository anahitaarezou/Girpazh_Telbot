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

# آیدی عددی ادمین (جایگزین با آیدی خودتان)
ADMIN_ID = 1066552638  # عدد آیدی تلگرام ادمین را اینجا قرار دهید

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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

def get_navigation_markup(current_step):
    keyboard = []
    if current_step > ASK_MODEL:
        keyboard.append([InlineKeyboardButton("⬅️ بازگشت به مرحله قبل", callback_data="prev_step")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
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

async def ask_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def ask_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
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

async def finalize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        return ASK_CHASSIS
    if update.message and update.message.text:
        user = update.effective_user
        context.user_data["chassis"] = update.message.text.strip()
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

        # ارسال اطلاعات کاربر به ادمین
        admin_message = (
            "📥 درخواست جدید قطعه خودرو:\n"
            f"👤 کاربر: @{user.username or user.first_name}\n"
            f"🆔 آیدی: {user.id}\n"
            f"• مدل: {context.user_data['model']}\n"
            f"• سال ساخت: {context.user_data['year']}\n"
            f"• قطعه: {context.user_data['part']}\n"
            f"• شماره شاسی: {context.user_data['chassis']}\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
        except Exception as e:
            logging.error(f"Error sending message to admin: {e}")

        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❗️لطفاً شماره شاسی را به صورت صحیح وارد کنید.",
            reply_markup=get_navigation_markup(ASK_CHASSIS)
        )
        return ASK_CHASSIS

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        about_text = (
            "📌 گیرپاژ، نتیجه‌ی ۵۰ سال تجربه در بازار قطعات یدکی و بهره‌گیری از فناوری‌های روز است.\n"
            "مجموعه‌ای از قطعات دارای شناسه کالا، کد رهگیری و گارانتی معتبر، اصالت، کیفیت و قیمت مناسب را به شما ارائه می‌دهد.\n"
            "با ما در تماس باشید و از خدمات ما بهره‌مند شوید.\n\n"
            f"👤 آیدی ادمین: <code>{ADMIN_ID}</code>"
        )
        await query.edit_message_text(
            about_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 آدرس سایت", url="https://pm2.girpazh.com/contact")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ]),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    elif query.data == "main_menu":
        await start(update, context)
        return ConversationHandler.END
    elif query.data == "start_form":
        return await ask_model(update, context)
    elif query.data == "show_phone":
        keyboard = [
            [InlineKeyboardButton("🌐 صفحه تماس سایت", url="https://pm2.girpazh.com/contact")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "☎ برای تماس با پشتیبانی با شماره 09928642905 تماس بگیرید یا به صفحه تماس سایت مراجعه کنید.\n",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return ConversationHandler.END
    elif query.data == "prev_step":
        current_step = context.user_data.get("current_step", ASK_MODEL)
        if current_step == ASK_YEAR:
            await query.edit_message_text(
                "مرحله ۱: مدل خودرو را وارد کنید:",
                reply_markup=get_navigation_markup(ASK_MODEL)
            )
            context.user_data["current_step"] = ASK_MODEL
            return ASK_MODEL
        elif current_step == ASK_PART:
            await query.edit_message_text(
                "مرحله ۲: سال ساخت خودرو را وارد کنید:",
                reply_markup=get_navigation_markup(ASK_YEAR)
            )
            context.user_data["current_step"] = ASK_YEAR
            return ASK_YEAR
        elif current_step == ASK_CHASSIS:
            await query.edit_message_text(
                "مرحله ۳: نام قطعه موردنظر را وارد کنید:",
                reply_markup=get_navigation_markup(ASK_PART)
            )
            context.user_data["current_step"] = ASK_PART
            return ASK_PART
        else:
            await start(update, context)
            return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token("7724167611:AAGYSWUpQK90jrF57DRk5mto32dn65GuosU").build()  # توکن ربات خود را جایگزین کنید

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
