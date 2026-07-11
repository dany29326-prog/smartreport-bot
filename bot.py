import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from sheets import GoogleSheetsManager

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')
sheet_manager = None

try:
    if SERVICE_ACCOUNT_JSON:
        sheet_manager = GoogleSheetsManager(SERVICE_ACCOUNT_JSON)
        logger.info("✅ Connected to Google Sheets with Service Account")
    else:
        sheet_manager = GoogleSheetsManager()
        logger.info("✅ Connected to Google Sheets with local file")
except Exception as e:
    logger.error(f"❌ Failed to connect to Google Sheets: {str(e)}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = (
        f"Halo {user.first_name}! 👋\n\n"
        "Aku adalah SmartReport Bot untuk mencatat pengeluaran.\n\n"
        "📝 **Cara Penggunaan:**\n"
        "/tambah [jumlah] [nama] [kategori] [keterangan]\n"
        "/lihat - Lihat 10 pengeluaran terakhir\n"
        "/total - Lihat total pengeluaran\n"
        "/help - Tampilkan bantuan\n\n"
        "💡 **Contoh:**\n"
        "/tambah 25000 Andi Makan Makan siang\n"
        "/tambah 15000 Budi Transport Bensin motor"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 **Daftar Perintah:**\n\n"
        "/start - Mulai bot\n"
        "/tambah [jumlah] [nama] [kategori] [keterangan]\n"
        "/lihat - Lihat 10 pengeluaran terakhir\n"
        "/total - Lihat total pengeluaran\n"
        "/help - Tampilkan bantuan\n\n"
        "📝 **Format /tambah:**\n"
        "/tambah [jumlah] [nama] [kategori] [keterangan]\n\n"
        "💡 **Contoh:**\n"
        "/tambah 25000 Andi Makan Makan siang\n"
        "/tambah 15000 Budi Transport Bensin motor"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def tambah_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        
        if len(args) < 4:
            await update.message.reply_text(
                "❌ Format salah!\n"
                "/tambah [jumlah] [nama] [kategori] [keterangan]\n\n"
                "💡 Contoh: /tambah 25000 Andi Makan Makan siang"
            )
            return
        
        try:
            amount = float(args[0].replace('.', '').replace(',', ''))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await update.message.reply_text("❌ Jumlah tidak valid. Masukkan angka positif.")
            return
        
        name = args[1]
        category = args[2]
        description = ' '.join(args[3:])
        
        if sheet_manager:
            result = sheet_manager.add_expense(amount, name, category, description)
            
            response = (
                f"✅ Pengeluaran berhasil dicatat!\n\n"
                f"👤 {name}\n"
                f"💰 Rp{amount:,.0f}\n"
                f"📂 {category}\n"
                f"📝 {description}\n"
                f"📅 {result['date']}\n"
                f"🕐 {result['timestamp']}"
            )
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("❌ Koneksi ke Google Sheets gagal.")
            
    except Exception as e:
        logger.error(f"Error in tambah_command: {str(e)}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")

async def lihat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not sheet_manager:
            await update.message.reply_text("❌ Koneksi ke Google Sheets gagal.")
            return
        
        expenses = sheet_manager.get_expenses(limit=10)
        
        if not expenses:
            await update.message.reply_text(
                "📊 Belum ada pengeluaran yang tercatat.\n\n"
                "Mulai catat dengan:\n"
                "/tambah [jumlah] [nama] [kategori] [keterangan]"
            )
            return
        
        response = "📊 **10 Pengeluaran Terakhir:**\n\n"
        for i, exp in enumerate(expenses, 1):
            response += (
                f"{i}. 👤 {exp['Nama']} - Rp{float(exp['Jumlah']):,.0f}\n"
                f"   📂 {exp['Kategori']} | 📅 {exp['Tanggal']}\n"
                f"   📝 {exp['Keterangan']}\n\n"
            )
        
        total = sheet_manager.get_total_expenses()
        response += f"💰 **Total Pengeluaran:** Rp{total:,.0f}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in lihat_command: {str(e)}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")

async def total_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not sheet_manager:
            await update.message.reply_text("❌ Koneksi ke Google Sheets gagal.")
            return
        
        total = sheet_manager.get_total_expenses()
        
        if total == 0:
            await update.message.reply_text("📊 Belum ada pengeluaran yang tercatat.")
        else:
            await update.message.reply_text(f"💰 **Total Pengeluaran:** Rp{total:,.0f}")
            
    except Exception as e:
        logger.error(f"Error in total_command: {str(e)}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_TOKEN not found in environment variables")
        return
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tambah", tambah_command))
    application.add_handler(CommandHandler("lihat", lihat_command))
    application.add_handler(CommandHandler("total", total_command))
    
    logger.info("🚀 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()