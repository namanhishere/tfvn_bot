import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio

class BirthdayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.birthday_channel_id = self.bot.global_vars.get("BIRTHDAY_CHANNEL")
        if not self.birthday_channel_id:
            raise ValueError("BIRTHDAY_CHANNEL not set in global variables.")
        self.check_birthdays.start()  # Start the daily task

    def cog_unload(self):
        self.check_birthdays.cancel()  # Stop the task when the cog is unloaded

    @tasks.loop(seconds=5)  # Run every 24 hours
    async def check_birthdays(self):
        """Daily task to check and announce birthdays."""
        now = discord.utils.utcnow()
        current_date = now.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD for DB
        current_month = now.month
        current_day = now.day

        # Check if birthdays have already been announced today
        if self.db["birthday_announcements"].find_one({"date": current_date}):
            return  # Already announced, skip

        # Query DB for birthdays matching today
        birthdays_today = list(self.db["birthdays"].find({
            "month": current_month,
            "day": current_day
        }))

        if not birthdays_today:
            return  # No birthdays today

        # Get the channel
        channel = self.bot.get_channel(int(self.birthday_channel_id))
        if not channel:
            print("Birthday channel not found.")
            return

        # Send messages for each birthday
        for birthday in birthdays_today:
            user_id = birthday["user_id"]
            user = self.bot.get_user(user_id)
            if user:
                embed = discord.Embed(
                    title="🎉 Chúc Mừng Sinh Nhật! 🎂",
                    description=f"Hôm nay là sinh nhật của {user.mention}! Chúc bạn một ngày vui vẻ và tràn đầy tiếng cười! 🥳",
                    color=discord.Color.gold()
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                await channel.send(embed=embed)
            else:
                await channel.send(f"🎉 Hôm nay là sinh nhật của <@{user_id}>! (Không tìm thấy user)")

        # Mark as announced for today
        self.db["birthday_announcements"].insert_one({"date": current_date, "announced": True})

    @commands.group(name="birthday")
    async def birthday(self, ctx: commands.Context):
        """ Guide to set your birthday. """
        embed = discord.Embed(
            title="🎂 Đặt Sinh Nhật Của Bạn 🎉",
            description="Dùng lệnh sau để đặt sinh nhật của bạn:\n`!birthday set <ngày> <tháng>`\nVí dụ: `!birthday set 15 6` để đặt sinh nhật vào ngày 15 tháng 6.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @birthday.command(name="set")
    async def set_birthday(self, ctx: commands.Context, day: int, month: int):
        """Set your birthday (MM DD)."""
        if not (1 <= month <= 12):
            await ctx.send("Tháng phải từ 1 đến 12.")
            return
        if not (1 <= day <= 31):
            await ctx.send("Ngày phải từ 1 đến 31.")
            return
        
        # Basic validation (could add more for leap years, etc.)
        self.db["birthdays"].update_one(
            {"user_id": ctx.author.id},
            {"$set": {"month": month, "day": day}},
            upsert=True
        )
        await ctx.send(f"Đã đặt sinh nhật của bạn là {day}/{month}. 🎂")

async def setup(bot: commands.Bot):
    await bot.add_cog(BirthdayCog(bot))