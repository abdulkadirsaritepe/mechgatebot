# Import necessary libraries
import discord, json, sys
from discord.ext.commands import Bot

# Import mechgate's function files
from cogs.doorCheck import DoorCheck, DatabaseCommands
from cogs.console import Console
from cogs.rpi import RPi

if sys.platform == "linux":
	rpi_os = True
	import RPi.GPIO as GPIO
	mainDir = "/home/pi/asbot/mechgate" #! 
	logDir = "/home/pi/asbot/mechgate/cogs/Logs" #! 
	adminLogDir = f'{logDir}/admin.json'
else:
	GPIO = None
	rpi_os = False
	mainDir = "C:/Dev/Github/src/mechgate"
	logDir = "C:/Dev/Github/src/mechgate/cogs/Logs"
	adminLogDir = f'{logDir}/admin.json'

name = "mechgate"
with open(adminLogDir) as adminLogFile:
	data = json.load(adminLogFile)
bot_name = (data[name])["name"]
bot_prefix = (data[name])["prefix"]
bot_token = (data[name])["token"]

# For using some discord features, enable some properties
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.presences = True

# Define bot, and give its prefix and intents
client = Bot(command_prefix=bot_prefix, intents=intents)

# Remove help command
client.remove_command('help')

# Start console and RPi classes
console = Console(client, bot_name, logDir=logDir)
rpi = RPi(logDir=logDir)

# Runs when bot has connected
@client.event
async def on_connect():
	print('waiting...')
	# waiting until the bot is ready.
	await client.wait_until_ready()
	# getting console webhook
	await console.get_channel()
	# after bot is ready, the function finishes.
	print(f'{bot_name} is ready.')
	await console.print_console(level=1, number='9990', logText=f'{bot_name} has been started.')

# when the bot is ready, it changes its activity string.
@client.event
async def on_ready():
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="🚪"))

# Add imported functions
client.add_cog(DatabaseCommands(client, bot_name, console, rpi=rpi, logDir=logDir))
client.add_cog(DoorCheck(client, bot_name, console, rpi=rpi, logDir=logDir))

@client.command()
async def help(ctx):
	helpMessage = "Selam ben **Mech Gate**, \nOdtü Makina ve İnovasyon Topluluğu discord sunucusunda topluluk odasına giren çıkanları denetlemekten sorumluyum 😎."
	adminHelpMessage = f"Eğer yetkiniz var ise giriş çıkış yapabilecek kişilerin listesini düzenleyebilirsiniz. Gerekli komutları aşağıda bulabilirsin.\n\n**1- {bot_prefix}listmembers :** kapıya erişim ile ilgili daha önceden eklediğin kişilerin olduğu listeyi mesaj olarak almak için kullanabilirsin.\n**2- {bot_prefix}addmember [durum pozisyon isim soyisim kartnumarası]:** giriş yapabilmesini istediğin kişiyi eklemek için kullanabilirsin. Köşeli parantez içindeki bilgileri köşeli parantez olmadan atmalısın. *Örnek; {bot_prefix}addmember Active Member Test Test 123456789* . Ayrıca, durum için Active veya Passive, Pozisyon için Member veya Board kullanmanı tavsiye ederim.\n**3- {bot_prefix}removemember [anahtarkelime]:** listeden birini silmek istiyorsan bu komutu kullanabilirsin. Anahtar kelime olarak isim kullanmalısın. Eğer aynı isimde birden fazla kişi varsa anahtar kelime bölümüne isim soyisim yazabilirsin. *Örnek; {bot_prefix}removemember Test, {bot_prefix}removemember Test Test* . Ek olarak, büyük küçük harflere duyarlıyım, dikkat et lütfen.\n\n**Not:** Kısa bir hatırlatma, listeye kişi eklerken kişinin kart numarasına ihtiyacın var. Bu numarayı kartı kapı girişine okutarak erişebilirsin. Kartı okuttuğunda sunucudaki daha önceden belirlenmiş kanala bildirim gelecek. O mesajdan numarayı alarak ekleme yapabilirsin."
	await ctx.send(f'{helpMessage}\n\n\n{adminHelpMessage}')

@client.command()
async def close(ctx):
	author = int(ctx.author.id)
	with open(adminLogDir) as adminLogFile:
		data = json.load(adminLogFile)
	if author == int(data["superadmin_id"]):
		await console.print_console(level=1, logText=f'Trying to close {bot_name}...')
		await ctx.message.delete()
		if GPIO != None:
			rpi.quit_rpi()
		await client.close()

# Start the bot
client.run(bot_token)

#BOT_SECRET
