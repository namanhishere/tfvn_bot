import discord 
from discord.ext import commands
import datetime
import asyncio

class HappyLunarNewYear2026CommandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.start_time = datetime.datetime(2026, 2, 16, 17, 0, 0, tzinfo=datetime.timezone.utc)  # 00:00 UTC+7 on Feb 16, 2026 (17:00 UTC on Feb 15, 2026)
        self.end_time = datetime.datetime(2026, 2, 17, 17, 0, 0, tzinfo=datetime.timezone.utc)  # 00:00 UTC+7 on Feb 17, 2026 (17:00 UTC on Feb 16, 2026)
    
    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.author == self.bot.user:
            return
        
        # needing it have keyword "năm mới", "nmvv", 2026, happy new year in message
        if not any(keyword in ctx.content.lower() for keyword in ["năm mới", "nmvv", "2026", "new year"]):
            return
        
        # this bot will work from 2026-02-16 00:00 UTC to 2026-02-17 17:00 UTC
        now = datetime.datetime.now(datetime.timezone.utc)

        if not (self.start_time <= now <= self.end_time):
            return
        
        # check if that user have received the greeting already
        record = self.db["happy_lunar_new_year_2026"].find_one({"user_id": ctx.author.id})
        if record:
            return
        
        # send greeting message
        await ctx.reply(
            f"Chúc mừng năm mới năm Bính Ngọ 2026 {ctx.author.mention}! 🎉🎊\n"
            f"Chúc bạn năm mới giỏi giang hơn nè, giàu sang hơn nè, và ngày càng xinh xắnnn, đáng yêu hếttt phần thiên hạ luôn nha UwU 🥳 \n"
            f"Cảm ơn bạn vì đã ở đây và là một mảnh ghép siêu quan trọng của server, thương bạn nhiều ơi là nhiều luôn óoooo  ❣️ ❣️ ❣️ \n"
            f"Năm mới hy vọng được tương tác với nhau nhiều hơn nhóoooooo 😘"
        )

        # record that the greeting has been sent
        self.db["happy_lunar_new_year_2026"].insert_one({"user_id": ctx.author.id, "timestamp": now})
        
async def setup(bot: commands.Bot):
    await bot.add_cog(HappyLunarNewYear2026CommandCog(bot))