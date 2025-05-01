from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
import csv
from datetime import datetime
import re
import os
import logging

# تنظیمات لاگ
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# مراحل فرم
ASK_CHASSIS, ASK_MODEL, ASK_YEAR, ASK_PART = range(4)

# تابع شروع ربات (منوی اصلی)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name
    keyboard = [
        [InlineKeyboardButton("🚘 شروع ثبت اطلاعات خودرو", callback_data="start_form")],
        [InlineKeyboardButton("📞 تماس با پشتیبانی", callback_data="call_support")],
        [InlineKeyboardButton("💬 چت با پشتیبانی", callback_data="chat_support")],
        [InlineKeyboardButton("ℹ درباره ما", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = f"سلام {name} عزیز! 👋\nبه ربات پشتیبانی گیرپاژ خوش آمدید.\nلطفاً یکی از گزینه‌ها را انتخاب کنید:"
    
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_message, reply_markup=reply_markup)
    return ConversationHandler.END  # اطمینان از پایان هر مکالمه قبلی

# دکمه بازگشت به منوی اصلی
def get_back_to_menu_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_menu")]])

# اعتبارسنجی سال ساخت (باید عدد چهار رقمی باشد)
def validate_year(year_text):
    return bool(re.match(r'^\d{4}$', year_text))

# اعتبارسنجی شماره شاسی (باید دقیقاً 17 رقم باشد)
def validate_chassis(chassis_text):
    return bool(re.match(r'^\d{17}$', chassis_text))

# مرحله 1: دریافت شماره شاسی
async def ask_chassis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        await update.message.reply_text(
            "⚠ لطفاً فقط متن وارد کنید (مثلاً شماره شاسی یا «ندارم»).",
            reply_markup=get_back_to_menu_button()
        )
        return ASK_CHASSIS
    
    chassis = update.message.text.strip()
    
    if chassis.lower() in ["ندارم", "نامشخص", "نمیدانم"]:
        support_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 تماس مستقیم با پشتیبانی", url="tel:+989928642905")],
            [InlineKeyboardButton("💬 ارسال پیام به پشتیبانی", callback_data="start_support_chat")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_menu")]
        ])
        
        await update.message.reply_text(
            "⛔ متأسفیم، بدون شماره شاسی نمی‌توانیم درخواست شما را پردازش کنیم.\n\n"
            "🔹 راه‌های دریافت شماره شاسی:\n"
            "1. بررسی کارت خودرو\n"
            "2. بررسی بدنه خودرو (معمولاً در موتور یا درب راننده)\n"
            "3. تماس با نمایندگی\n\n"
            "📞 می‌توانید از گزینه‌های زیر برای ارتباط با پشتیبانی استفاده کنید:",
            reply_markup=support_keyboard,
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    if not validate_chassis(chassis):
        await update.message.reply_text(
            "⚠ شماره شاسی باید دقیقاً 17 رقم باشد. لطفاً دوباره وارد کنید:",
            reply_markup=get_back_to_menu_button()
        )
        return ASK_CHASSIS
    
    context.user_data["chassis"] = chassis
    await update.message.reply_text(
        "✅ شماره شاسی ثبت شد.\n"
        "مرحله 2⃣: لطفاً مدل خودرو را وارد کنید (مثال: تیبا 2):",
        reply_markup=get_back_to_menu_button()
    )
    return ASK_MODEL

# مرحله 2: مدل خودرو
async def ask_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        await update.message.reply_text(
            "⚠ لطفاً فقط متن وارد کنید (مثلاً مدل خودرو).",
            reply_markup=get_back_to_menu_button()
        )
        return ASK_MODEL
    context.user_data["model"] = update.message.text.strip()
    await update.message.reply_text(
        "مرحله 3⃣: سال ساخت خودرو را وارد کنید (مثال: 1398):",
        reply_markup=get_back_to_menu_button()
    )
    return ASK_YEAR

# مرحله 3: سال ساخت
async def ask_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        await update.message.reply_text(
            "⚠ لطفاً فقط متن وارد کنید (مثلاً سال ساخت).",
            reply_markup=get_back_to_menu_button()
        )
        return ASK_YEAR
    year_text = update.message.text.strip()
    if not validate_year(year_text):
        await update.message.reply_text(
            "⚠ سال ساخت باید یک عدد چهار رقمی باشد (مثال: 1398). لطفاً دوباره وارد کنید:",
            reply_markup=get_back_to_menu_button()
        )
        return ASK_YEAR
    context.user_data["year"] = year_text
    await update.message.reply_text(
        "مرحله 4⃣: نام قطعه موردنظر را وارد کنید:",
        reply_markup=get_back_to_menu_button()
    )
    return ASK_PART

# مرحله 4: نام قطعه
async def ask_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        await update.message.reply_text(
            "⚠ لطفاً فقط متن وارد کنید (مثلاً نام قطعه).",
            reply_markup=get_back_to_menu_button()
        )
        return ASK_PART
    context.user_data["part"] = update.message.text.strip()
    
    # نمایش اطلاعات واردشده توسط کاربر
    user_data = context.user_data
    reply = (
        "✅ اطلاعات شما با موفقیت ثبت شد:\n"
        f"🔹 شماره شاسی: {user_data.get('chassis', 'ندارد')}\n"
        f"🔹 مدل خودرو: {user_data['model']}\n"
        f"🔹 سال ساخت: {user_data['year']}\n"
        f"🔹 نام قطعه: {user_data['part']}\n\n"
        "درخواست شما ثبت شد و بررسی می‌گردد. با شما تماس خواهیم گرفت."
    )
    
    await update.message.reply_text(reply, reply_markup=get_back_to_menu_button())
    
    # ذخیره اطلاعات در فایل CSV
    csv_file = 'requests.csv'
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:  # اگر فایل وجود ندارد، هدر را اضافه کن
            writer.writerow(["User ID", "Chassis", "Model", "Year", "Part", "Timestamp"])
        writer.writerow([
            update.effective_user.id,
            user_data.get('chassis', 'ندارد'),
            user_data['model'],
            user_data['year'],
            user_data['part'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # پیام اطلاعات برای ارسال به گروه پشتیبانی و ادمین
    request_message = (
        "📩 درخواست جدید:\n"
        f"🔹 کاربر: {update.effective_user.id}\n"
        f"🔹 شماره شاسی: {user_data.get('chassis', 'ندارد')}\n"
        f"🔹 مدل خودرو: {user_data['model']}\n"
        f"🔹 سال ساخت: {user_data['year']}\n"
        f"🔹 نام قطعه: {user_data['part']}"
    )
    
    # ارسال اطلاعات به گروه پشتیبانی
    support_chat_id = "CHAT_ID"  # آیدی گروه پشتیبانی (این مقدار را تغییر دهید)
    try:
        await context.bot.send_message(chat_id=support_chat_id, text=request_message)
    except Exception as e:
        logging.error(f"خطا در ارسال به گروه پشتیبانی: {e}")
    
    # ارسال اطلاعات به ادمین
    admin_chat_id = "ADMIN_CHAT_ID"  # آیدی ادمین (این مقدار را تغییر دهید)
    try:
        await context.bot.send_message(chat_id=admin_chat_id, text=request_message)
    except Exception as e:
        logging.error(f"خطا در ارسال به ادمین: {e}")
    
    return ConversationHandler.END

# هندلر شروع چت با پشتیبانی
async def start_support_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    support_chat_url = "https://t.me/gearage_support"  # جایگزین کنید با آیدی واقعی پشتیبانی
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 شروع چت در تلگرام", url=support_chat_url)],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]
    ])
    
    await query.edit_message_text(
        "🔹 برای چت با پشتیبانی لطفاً روی دکمه زیر کلیک کنید:\n\n"
        "ساعات پاسخگویی: ۹ صبح تا ۵ عصر\n"
        "پاسخگویی در کمتر از ۱ ساعت کاری",
        reply_markup=keyboard
    )

# هندلر تماس با پشتیبانی
async def call_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 تماس مستقیم", url="tel:+989928642905")],
        [InlineKeyboardButton("📝 ارسال شماره تماس", callback_data="share_phone")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]
    ])
    
    await query.edit_message_text(
        "☎ راه‌های تماس با پشتیبانی:\n\n"
        "🔹 شماره تماس: 09928642905\n"
        "🔹 ساعات تماس: ۹ صبح تا ۵ عصر\n\n"
        "می‌توانید از دکمه زیر برای تماس مستقیم استفاده کنید:",
        reply_markup=keyboard
    )

# هندلر اشتراک‌گذاری شماره تماس
async def share_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً شماره تماس خود را ارسال کنید یا از دکمه اشتراک‌گذاری شماره استفاده نمایید.\n\n"
        "پشتیبانی در اولین فرصت با شما تماس خواهد گرفت.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="call_support")]
        ])
    )

# مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "about":
        await query.edit_message_text(
            "📌 این ربات جهت ثبت سفارش قطعات خودروی شما طراحی شده است.",
            reply_markup=get_back_to_menu_button()
        )
    elif query.data == "start_form":
        await query.edit_message_text(
            "مرحله 1⃣: لطفاً شماره شاسی خودرو را وارد کنید یا بنویسید «ندارم» (شماره شاسی باید 17 رقم باشد):",
            reply_markup=get_back_to_menu_button()
        )
        return ASK_CHASSIS
    elif query.data == "back_to_menu":
        await start(update, context)
        return ConversationHandler.END

# لغو گفتگو
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔ ثبت اطلاعات لغو شد.", reply_markup=ReplyKeyboardRemove())
    await start(update, context)  # بازگشت به منوی اصلی پس از لغو
    return ConversationHandler.END

# مدیریت پیام‌های غیرمتن
async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠ لطفاً فقط متن وارد کنید. برای لغو، از دستور /cancel استفاده کنید.",
        reply_markup=get_back_to_menu_button()
    )

# اجرای برنامه
def main():
    application = ApplicationBuilder().token("7724167611:AAGYSWUpQK90jrF57DRk5mto32dn65GuosU").build()
    
    # مکالمه چندمرحله‌ای
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^start_form$"),
            CommandHandler('start', start)
        ],
        states={
            ASK_CHASSIS: [MessageHandler(filters.TEXT & filters.COMMAND, ask_chassis)],
            ASK_MODEL: [MessageHandler(filters.TEXT & filters.COMMAND, ask_model)],
            ASK_YEAR: [MessageHandler(filters.TEXT & filters.COMMAND, ask_year)],
            ASK_PART: [MessageHandler(filters.TEXT & filters.COMMAND, ask_part)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(button_handler, pattern="^back_to_menu$"),
            MessageHandler(filters.ALL & ~filters.TEXT, handle_non_text)  # مدیریت پیام‌های غیرمتن
        ],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(start_support_chat, pattern="^start_support_chat$"))
    application.add_handler(CallbackQueryHandler(call_support, pattern="^call_support$"))
    application.add_handler(CallbackQueryHandler(share_phone, pattern="^share_phone$"))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ ربات آماده است...")
    application.run_polling()

if __name__ == '__main__':
    main()
