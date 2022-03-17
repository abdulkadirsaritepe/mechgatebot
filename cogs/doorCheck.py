
from discord.ext.commands import Cog, command
from discord.ext import commands, tasks
import discord, sys
import texttable, json
from threading import Thread

from cogs.rpi import RPi

class DoorCheck(Cog):
    def __init__(self, bot, bot_name, console, rpi, logDir):
        self.bot = bot
        self.bot_name = str(bot_name).lower()
        self.logDir = logDir
        self.doorLogGuildId = 0
        if sys.platform == "linux":
            self.rpi_os = True
        else:
            self.rpi_os = False
        self.adminLogDir = f'{self.logDir}/admin.json'
        self.commandLogDir = f'{self.logDir}/commands.json'
        self.logs = {}
        self.console = console
        self.doorStatusNotificationChannelId = None
        self.doorStatusNotificationChannel = None
        self.doorStatus = "open"
        self.rpi = rpi

    @Cog.listener()
    async def on_ready(self):
        with open(self.commandLogDir) as logs_file:
            self.logs = json.load(logs_file)
        try:
            await self.initializeDoorLog(self.doorLogGuildId)
            await self.console.print_console(level=2, number="0001", logText=f'Door log is initialized!')
            if self.rpi_os:
                await self.console.print_console(level=2, number="0002", logText=f'Door check has been started.')
                self.door_check.start()
            else:
                await self.console.print_console(level=2, number="0001", logText=f'Door check could not been started.')
        except:
            self.rpi_os = False
            await self.console.print_console(level=3, number="0001", logText=f'Door log cannot be initialized!')

    async def initializeDoorLog(self, guildId):
        guild = self.bot.get_guild(id=int(guildId))
        if guild:
            self.doorStatusNotificationChannelId = (self.logs["doorStatusNotificationChannels"])[str(guildId)]
        self.doorStatusNotificationChannel = guild.get_channel(int(self.doorStatusNotificationChannelId))

    @tasks.loop(seconds=2.0)
    async def door_check(self):
        trespassing, result = self.rpi.mech_door()
        if trespassing != None:
            try:
                if self.doorStatus == "open":
                    if trespassing:
                        member = result[0]
                        await self.doorStatusNotificationChannel.send(f'**{member}** tarafından topluluk odası kapısı açıldı.')
                        self.rpi.open_door()
                    elif trespassing == False:
                        cardid = result
                        await self.doorStatusNotificationChannel.send(f'Kart numarası **{cardid}** olan birisi topluluk odası kapısını açmaya çalıştı.')
                else:
                    if trespassing:
                        member = result[0]
                        await self.doorStatusNotificationChannel.send(f'**{member}** tarafından topluluk odası kapısı açılmaya çalışıldı, kapı kilitli olduğu için kapı açılmadı.')
                    else:
                        cardid = result
                        await self.doorStatusNotificationChannel.send(f'Kart numarası **{cardid}** olan birisi topluluk odası kapısını açmaya çalıştı.')
            except:
                pass

    @command()
    @commands.has_permissions(manage_channels=True)
    async def doorlock(self, ctx, status="close"):
        if str(status).lower() != "open" and str(status).lower() != "close":
            await ctx.send("Invalid keyword!")
        else:
            self.doorStatus = status
            if str(status).lower() == "open":
                await ctx.send("Kapı kilidi açıldı!")
            elif str(status).lower() == "close":
                await ctx.send("Kapı kilitlendi!")
        await ctx.message.delete()

    @door_check.before_loop
    async def before_check(self):
        # waits until the bot is ready, then it starts the loop.
        await self.bot.wait_until_ready()
    
class DatabaseCommands(Cog):
    def __init__(self, bot, bot_name, console, rpi, logDir):
        self.bot = bot
        self.bot_name = str(bot_name).lower()
        self.logDir = logDir
        self.doorLogGuildId = 699224778824745003 # TODO 743711488220594217 699224778824745003
        if sys.platform == "linux":
            self.rpi_os = True
        else:
            self.rpi_os = False
        self.adminLogDir = f'{self.logDir}/admin.json'
        self.commandLogDir = f'{self.logDir}/commands.json'
        self.logs = {}
        self.console = console
        self.doorStatusNotificationChannelId = None
        self.rpi = rpi

    @Cog.listener()
    async def on_message(self, ctx):
        # * Mentioned in a message
        message = ctx
        if self.bot.user.mentioned_in(message):
            if message.channel.type != discord.ChannelType.private:
                await self.console.print_console(level=0, number="1009", logText=str(message.content))

    @command()
    @commands.has_permissions(manage_channels=True)
    async def listmembers(self, ctx):
        members = self.rpi.list_members()
        message_list = []
        member_list = [["Durum", "Pozisyon", "İsim", "Soyisim", "Kart Numarası"]]
        n = 0
        for member in members:
            if n == 10:
                message_list.append(member_list)
                member_list = [["Durum", "Pozisyon", "İsim", "Soyisim", "Kart Numarası"]]
                n = 0
            member_list.append([member["status"], member["position"], member["name"], member["surname"], member["cardid"]])
            n+=1
        message_list.append(member_list)
        tableObj = texttable.Texttable()
        for msg in message_list:
            # Set columns
            tableObj.set_cols_align(["c", "c", "c", "c", "c"])
            # Set datatype of each column
            tableObj.set_cols_dtype(["t", "t", "t", "t", "i"])
            # Adjust columns
            tableObj.set_cols_valign(["m", "m", "m", "m", "m"])
            # Insert rows
            tableObj.add_rows(msg)
            await ctx.send(f'```{tableObj.draw()}```')
            tableObj.reset()

    @command()
    @commands.has_permissions(manage_channels=True)
    async def addmember(self, ctx, status, position, name, surname, cardid):
        self.rpi.add_member(status, position, name, surname, cardid)
        await ctx.send("Kişi veri tabanına eklendi.")

    @command()
    @commands.has_permissions(manage_channels=True)
    async def removemember(self, ctx, name=None, surname=None):
        if surname == None:
            result = self.rpi.remove_member(name)
            if result == 1:
                await ctx.send("Kişi veri tabanından silindi.")
            elif result == 2:
                await ctx.send("Aynı kriterlere uygun birden fazla kişi bulunuyor.")
            else:
                await ctx.send("Kriterlere uygun kişi bulunamadı.")
        else:
            self.rpi.remove_member(name, surname)
            await ctx.send("Kişi veri tabanından silindi.")
    
    @command()
    async def getcommands(self, ctx):
        for item in self.bot.commands:
            await ctx.send(item.name)

    @command()
    async def testCmd(self, ctx):
        await ctx.message.delete()
        await ctx.send(self.doorStatusNotificationChannelId)
