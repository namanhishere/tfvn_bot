import discord
from discord.ext import commands
from datetime import timedelta

class JanitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clean_before")
    @commands.has_permissions(manage_messages=True)
    async def clean_messages_created_before(self, ctx: commands.Context, days: int):
        """Delete messages created before a specified number of days."""
        if days < 0:
            await ctx.send("Số ngày không thể là số âm.")
            return

        cutoff = discord.utils.utcnow() - timedelta(days=days)
        def is_older_than_cutoff(message):
            return message.created_at < cutoff

        deleted = await ctx.channel.purge(check=is_older_than_cutoff)
        await ctx.send(f"Đã xóa {len(deleted)} tin nhắn được tạo trước {days} ngày.", delete_after=5)

async def setup(bot: commands.Bot):
    await bot.add_cog(JanitorCog(bot))