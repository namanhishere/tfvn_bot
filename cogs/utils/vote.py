import discord
from discord.ext import commands, tasks
import asyncio
import re
from datetime import datetime, timedelta

class VoteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db  # Assuming bot.db is your database connection
        self.check_ended_votes.start()  # Start the background task

    def cog_unload(self):
        self.check_ended_votes.cancel()

    def parse_time(self, time_str: str) -> int:
        """Parse time string like '1m', '2h', '1d' into seconds."""
        match = re.match(r'^(\d+)([mhd])$', time_str.lower())
        if not match:
            raise ValueError("Invalid time format. Use '1m' for 1 minute, '2h' for 2 hours, '1d' for 1 day.")
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        else:
            raise ValueError("Invalid unit. Use 'm', 'h', or 'd'.")


    @tasks.loop(minutes=1)  # Check every minute for ended votes
    async def check_ended_votes(self):
        """Background task to process ended votes."""
        now = discord.utils.utcnow()
        ended_votes = list(self.db["votes"].find({"end_time": {"$lte": now}}))

        for vote in ended_votes:
            await self._process_vote_results(vote)
            self.db["votes"].delete_one({"_id": vote["_id"]})  # Remove processed vote

    async def _process_vote_results(self, vote):
        """Process and send results for a ended vote."""
        channel = self.bot.get_channel(vote["channel_id"])
        if not channel:
            return

        try:
            vote_msg = await channel.fetch_message(vote["message_id"])
        except discord.NotFound:
            return  # Message deleted

        results = {}
        for reaction in vote_msg.reactions:
            emoji = str(reaction.emoji)
            count = reaction.count - 1  # Subtract bot's reaction
            if count > 0:
                results[emoji] = count

        embed = discord.Embed(title=f"Kết quả bỏ phiếu: {vote['question']}", color=discord.Color.blue())
        if vote["vote_type"] == "yesno":
            yes_count = results.get("✅", 0)
            no_count = results.get("❌", 0)
            embed.add_field(name="✅ Có", value=str(yes_count), inline=True)
            embed.add_field(name="❌ Không", value=str(no_count), inline=True)
        else:
            for idx, option in enumerate(vote["options"], start=1):
                emoji = f"{idx}\N{COMBINING ENCLOSING KEYCAP}"
                count = results.get(emoji, 0)
                embed.add_field(name=f"{idx}. {option}", value=str(count), inline=True)

        await channel.send(embed=embed)

    @commands.command(name='vote', help='Starts a vote with the given options.')
    async def vote(self, ctx, vote_type: str = "yesno", *, question: str = None):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        # If no question provided, ask for it
        if not question:
            await ctx.send("Vui lòng nhập câu hỏi cho cuộc bỏ phiếu:")
            try:
                question_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                question = question_msg.content
            except asyncio.TimeoutError:
                await ctx.send("Timeout! Cuộc bỏ phiếu đã bị hủy.")
                return

        await ctx.send("Cuộc bỏ phiếu kết thúc lúc nào? Vui lòng nhập thời gian (ví dụ: '1m' cho 1 phút, '2h' cho 2 giờ, '1d' cho 1 ngày)")
        try:
            time_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            time_str = time_msg.content
            duration_seconds = self.parse_time(time_str)
        except asyncio.TimeoutError:
            await ctx.send("Timeout! Cuộc bỏ phiếu đã bị hủy.")
            return
        except ValueError as e:
            await ctx.send(str(e))
            return

        vote_type = vote_type.lower()
        end_time = discord.utils.utcnow() + timedelta(seconds=duration_seconds)

        if vote_type == "yesno":
            vote_message = f"**{question}**\n✅ Có\n❌ Không"
            vote_msg = await ctx.send(vote_message)
            await vote_msg.add_reaction("✅")
            await vote_msg.add_reaction("❌")
            options = None
        
        elif vote_type in ["multiple", "multiplechoice"]:
            await ctx.send("Vui lòng nhập các lựa chọn (mỗi lựa chọn trên một dòng):")
            try:
                options_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                option_list = options_msg.content.splitlines()
                if len(option_list) < 2:
                    await ctx.send("Cần ít nhất 2 lựa chọn.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("Timeout! Cuộc bỏ phiếu đã bị hủy.")
                return

            vote_message = f"**{question}**\n"
            for idx, option in enumerate(option_list, start=1):
                vote_message += f"{idx}. {option}\n"

            vote_msg = await ctx.send(vote_message)
            for idx in range(1, min(len(option_list) + 1, 10)):
                await vote_msg.add_reaction(f"{idx}\N{COMBINING ENCLOSING KEYCAP}")
            options = option_list
        
        else:
            await ctx.send("Loại bỏ phiếu không hợp lệ. Sử dụng 'yesno' hoặc 'multiple'.")
            return

        # Store vote in DB
        self.db["votes"].insert_one({
            "message_id": vote_msg.id,
            "channel_id": ctx.channel.id,
            "end_time": end_time,
            "vote_type": vote_type,
            "question": question,
            "options": options
        })

        await ctx.send(f"Cuộc bỏ phiếu đã bắt đầu! Kết thúc trong {discord.utils.format_dt(end_time, style='R')}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))