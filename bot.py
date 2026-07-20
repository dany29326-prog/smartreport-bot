import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from sheets import GoogleSheetsManager
from datetime import datetime, timedelta

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
        "Aku adalah SmartReport Bot untuk mencatat keuangan.\n\n"
        "📝 **Cara Penggunaan:**\n"
        "/tambah [jenis] [nominal] [kategori] [keterangan]\n"
        "/summary - Ringkasan semua waktu\n"
        "/hari - Ringkasan hari ini\n"
        "/minggu - Ringkasan minggu ini\n"
        "/bulan - Ringkasan bulan ini\n"
        "/laporan [kategori] [periode]\n"
        "/help - Tampilkan bantuan\n\n"
        "💡 **Contoh:**\n"
        "/tambah pemasukan 5000000 Gaji Gaji bulanan\n"
        "/tambah pengeluaran 25000 Makan Makan siang\n"
        "/laporan Makan minggu ini"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 **Daftar Perintah:**\n\n"
        "/start - Mulai bot\n"
        "/tambah [jenis] [nominal] [kategori] [keterangan]\n"
        "/summary - Ringkasan semua waktu\n"
        "/hari - Ringkasan hari ini\n"
        "/minggu - Ringkasan minggu ini\n"
        "/bulan - Ringkasan bulan ini\n"
        "/laporan [kategori] [periode]\n"
        "/help - Tampilkan bantuan\n\n"
        "📝 **Contoh:**\n"
        "/tambah pemasukan 5000000 Gaji Gaji bulanan\n"
        "/tambah pengeluaran 25000 Makan Makan siang\n"
        "/laporan Makan minggu ini\n"
        "/laporan keuangan bulan ini"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def tambah_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        
        if len(args) < 4:
            await update.message.reply_text(
                "❌ Format:\n/tambah [jenis] [nominal] [kategori] [keterangan]\n\n"
                "Contoh:\n/tambah pemasukan 5000000 Gaji Gaji bulanan\n"
                "/tambah pengeluaran 25000 Makan Makan siang"
            )
            return
        
        trans_type = args[0].lower()
        if trans_type not in ['pemasukan', 'pengeluaran']:
            await update.message.reply_text("❌ Jenis harus 'pemasukan' atau 'pengeluaran'")
            return
        
        try:
            amount = float(args[1].replace('.', '').replace(',', ''))
            if amount <= 0:
                raise ValueError
        except:
            await update.message.reply_text("❌ Nominal harus angka positif")
            return
        
        category = args[2]
        description = ' '.join(args[3:])
        
        result = sheet_manager.add_transaction(trans_type, amount, category, description)
        
        emoji = "💰" if trans_type == "pemasukan" else "💸"
        response = (
            f"{emoji} {trans_type.title()} berhasil dicatat!\n\n"
            f"📂 {category}\n"
            f"Rp{amount:,.0f}\n"
            f"📝 {description}\n"
            f"📅 {result['date']}"
        )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error in tambah_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        summary = sheet_manager.get_summary()
        
        response = (
            "📊 **Ringkasan Keuangan:**\n\n"
            f"💰 Total Pemasukan: Rp{summary['total_masuk']:,.0f}\n"
            f"💸 Total Pengeluaran: Rp{summary['total_keluar']:,.0f}\n"
            f"📈 Saldo: Rp{summary['saldo']:,.0f}"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in summary_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def hari_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        transactions = sheet_manager.get_transactions(limit=1000)
        today = datetime.now().strftime("%Y-%m-%d")
        
        filtered = [t for t in transactions if t['Tanggal'] == today]
        
        total_masuk = sum(float(t['Pemasukan']) for t in filtered)
        total_keluar = sum(float(t['Pengeluaran']) for t in filtered)
        saldo = total_masuk - total_keluar
        
        response = (
            f"📊 **Ringkasan Hari Ini** ({today}):\n\n"
            f"💰 Pemasukan: Rp{total_masuk:,.0f}\n"
            f"💸 Pengeluaran: Rp{total_keluar:,.0f}\n"
            f"📈 Saldo: Rp{saldo:,.0f}"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in hari_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def minggu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        transactions = sheet_manager.get_transactions(limit=1000)
        now = datetime.now()
        start_of_week = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        
        filtered = [t for t in transactions if t['Tanggal'] >= start_of_week]
        
        total_masuk = sum(float(t['Pemasukan']) for t in filtered)
        total_keluar = sum(float(t['Pengeluaran']) for t in filtered)
        saldo = total_masuk - total_keluar
        
        response = (
            f"📊 **Ringkasan Minggu Ini** ({start_of_week} s.d {now.strftime('%Y-%m-%d')}):\n\n"
            f"💰 Pemasukan: Rp{total_masuk:,.0f}\n"
            f"💸 Pengeluaran: Rp{total_keluar:,.0f}\n"
            f"📈 Saldo: Rp{saldo:,.0f}"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in minggu_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def bulan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        transactions = sheet_manager.get_transactions(limit=1000)
        now = datetime.now()
        start_of_month = now.strftime("%Y-%m-01")
        
        filtered = [t for t in transactions if t['Tanggal'] >= start_of_month]
        
        total_masuk = sum(float(t['Pemasukan']) for t in filtered)
        total_keluar = sum(float(t['Pengeluaran']) for t in filtered)
        saldo = total_masuk - total_keluar
        
        response = (
            f"📊 **Ringkasan Bulan Ini** ({now.strftime('%B %Y')}):\n\n"
            f"💰 Pemasukan: Rp{total_masuk:,.0f}\n"
            f"💸 Pengeluaran: Rp{total_keluar:,.0f}\n"
            f"📈 Saldo: Rp{saldo:,.0f}"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in bulan_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def laporan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Format:\n/laporan [kategori] [periode]\n\n"
                "Contoh:\n/laporan Makan minggu ini\n/laporan keuangan bulan ini"
            )
            return
        
        keyword = args[0]
        periode = ' '.join(args[1:])
        
        transactions = sheet_manager.get_transactions(limit=1000)
        
        if keyword.lower() == 'keuangan':
            filtered = transactions
            title = "Keuangan"
        else:
            filtered = [t for t in transactions if t['Kategori'].lower() == keyword.lower()]
            title = keyword
        
        now = datetime.now()
        
        if "hari ini" in periode:
            date_filter = now.strftime("%Y-%m-%d")
            filtered = [t for t in filtered if t['Tanggal'] == date_filter]
            period_text = "Hari Ini"
        elif "minggu ini" in periode:
            start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
            filtered = [t for t in filtered if t['Tanggal'] >= start]
            period_text = "Minggu Ini"
        elif "bulan ini" in periode:
            start = now.strftime("%Y-%m-01")
            filtered = [t for t in filtered if t['Tanggal'] >= start]
            period_text = "Bulan Ini"
        else:
            period_text = periode
        
        if not filtered:
            await update.message.reply_text(f"📊 Tidak ada data untuk '{title}' {period_text}")
            return
        
        total_masuk = sum(float(t['Pemasukan']) for t in filtered)
        total_keluar = sum(float(t['Pengeluaran']) for t in filtered)
        saldo = total_masuk - total_keluar
        
        response = f"📊 Laporan {title} - {period_text}:\n\n"
        
        if keyword.lower() == 'keuangan':
            response += "💰 **PEMASUKAN:**\n"
            for t in filtered:
                if float(t['Pemasukan']) > 0:
                    response += f"  +Rp{float(t['Pemasukan']):,.0f} - {t['Keterangan']} ({t['Kategori']})\n"
            
            response += "\n💸 **PENGELUARAN:**\n"
            for t in filtered:
                if float(t['Pengeluaran']) > 0:
                    response += f"  -Rp{float(t['Pengeluaran']):,.0f} - {t['Keterangan']} ({t['Kategori']})\n"
        else:
            for t in filtered:
                if float(t['Pemasukan']) > 0:
                    response += f"  +Rp{float(t['Pemasukan']):,.0f} - {t['Keterangan']}\n"
                else:
                    response += f"  -Rp{float(t['Pengeluaran']):,.0f} - {t['Keterangan']}\n"
        
        response += f"\n📈 Total Pemasukan: Rp{total_masuk:,.0f}"
        response += f"\n📉 Total Pengeluaran: Rp{total_keluar:,.0f}"
        response += f"\n💰 Saldo: Rp{saldo:,.0f}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in laporan_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_TOKEN not found in environment variables")
        return
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tambah", tambah_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("hari", hari_command))
    application.add_handler(CommandHandler("minggu", minggu_command))
    application.add_handler(CommandHandler("bulan", bulan_command))
    application.add_handler(CommandHandler("laporan", laporan_command))
    
    logger.info("🚀 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()