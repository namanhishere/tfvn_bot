import asyncio
import discord  # pyright: ignore[reportMissingImports]
from datetime import datetime, timedelta

from discord.ext import commands  # pyright: ignore[reportMissingImports]
import random
from collections import deque

from assets.nsfw_gifs import (
    BLOWJOB_GIFS,
    HANDJOB_GIFS,
    RIMJOB_GIFS,
    FROTTING_GIFS,
    FUCKING_GIFS,
    CREAMPIE_GIFS,
)


# Tránh lặp gif đcmmmmmmm
class GifPicker:
    def __init__(self, gifs: list[str], history_size: int = 5):
        self.gifs = gifs
        self.recent = deque(maxlen=history_size)

    def pick(self) -> str:
        candidates = [g for g in self.gifs if g not in self.recent]
        gif = random.choice(candidates or self.gifs)
        self.recent.append(gif)
        return gif


class NSFWInteractionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bj_picker = GifPicker(BLOWJOB_GIFS, history_size=len(BLOWJOB_GIFS))
        self.hj_picker = GifPicker(HANDJOB_GIFS, history_size=len(HANDJOB_GIFS))
        self.rj_picker = GifPicker(RIMJOB_GIFS, history_size=len(RIMJOB_GIFS))
        self.frot_picker = GifPicker(FROTTING_GIFS, history_size=len(FROTTING_GIFS))
        self.fuck_picker = GifPicker(FUCKING_GIFS, history_size=len(FUCKING_GIFS))
        self.cream_picker = GifPicker(CREAMPIE_GIFS, history_size=len(CREAMPIE_GIFS))
        self.db = bot.db
        self.KING_ROLE_ID = None
        self.QUEEN_ROLE_ID = None

        if (
            self.bot.global_vars["KING_ROLE_ID"] is None or 
            self.bot.global_vars["KING_ROLE_ID"] == "" or
            self.bot.global_vars["QUEEN_ROLE_ID"] is None or
            self.bot.global_vars["QUEEN_ROLE_ID"] == ""
        ):
            raise ValueError("KING_ROLE_ID or QUEEN_ROLE_ID is not set in global variables.")
        
        KING_ROLE_ID = self.bot.global_vars["KING_ROLE_ID"]
        QUEEN_ROLE_ID = self.bot.global_vars["QUEEN_ROLE_ID"]
        try:
            self.KING_ROLE_ID = int(KING_ROLE_ID)  # Always convert to int
            self.QUEEN_ROLE_ID = int(QUEEN_ROLE_ID)  # Always convert to int
        except ValueError:
            raise ValueError("KING_ROLE_ID and QUEEN_ROLE_ID must be valid integers representing role IDs.")

    def is_king(self, member_roles: list[int]) -> bool:
        if self.KING_ROLE_ID in member_roles:
            return True
        
        return False
    
    def is_queen(self, member_roles: list[int]) -> bool:
        if self.QUEEN_ROLE_ID in member_roles:
            return True
        
        return False
    
    def check_if_user_is_locked(self, member_id: int) -> bool:
        is_locked = self.db["nsfw_settings"].find_one({
            "user_locked": member_id,
            "lock_until": {"$gte": datetime.utcnow()}
        })

        return is_locked is not None
    
    def get_remaining_lock_time(self, member_id: int) -> dict | None:
        lock_record = self.db["nsfw_settings"].find_one({
            "user_locked": member_id,
            "lock_until": {"$gte": datetime.utcnow()}
        })

        return lock_record if lock_record else None
    
    def format_relative_time_vn(self, dt: datetime) -> str:
        """Formats the relative time until the given datetime in Vietnamese style."""
        now = datetime.utcnow()
        diff = dt - now
        if diff.total_seconds() <= 0:
            return "đã hết"
        
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"trong {seconds} giây"
        minutes = seconds // 60
        if minutes < 60:
            return f"trong {minutes} phút"
        hours = minutes // 60
        if hours < 24:
            return f"trong {hours} giờ"
        days = hours // 24
        return f"trong {days} ngày"


    def record_action(self, action: str, ctx: commands.Context, member: discord.Member, coefficient: int = 1):
        document = {
            "message_id": ctx.message.id,
            "initMember": ctx.author.id,
            "targetMember": member.id,
            "action": action,
            "coefficient": coefficient,
            "created_at": datetime.utcnow(),
        }
        self.db["interactions"].insert_one(document)

    async def _nsfw_guard(self, ctx: commands.Context) -> bool:
        if ctx.channel.is_nsfw():
            return True

        await ctx.message.add_reaction("⚠️")
        warn_msg = await ctx.reply("🔞 Dùng lệnh này trong channel NSFW nhé.")
        await asyncio.sleep(5)
        await warn_msg.delete()
        await ctx.message.delete()
        return False

    async def _send_embed(
        self,
        ctx: commands.Context,
        *,
        title: str,
        description: str,
        gif_url: str,
        footer: str | None = None,
    ):
        embed = discord.Embed(
            title=title,
            description=description,
        )
        embed.set_image(url=gif_url)
        if footer:
            embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    # BLOWJOB
    @commands.command(name="bj")
    @commands.cooldown(1, 15, commands.BucketType.user)  # 1 use per 15 seconds per user
    async def blowjob(self, ctx: commands.Context, member: discord.Member):
        if not await self._nsfw_guard(ctx):
            return
        
        if member == ctx.author:
            await ctx.send("Bạn không thể tự bú cu mình được đâu 😳")
            return
        
        if (self.check_if_user_is_locked(ctx.author.id)):
            await ctx.send(f"{member.mention} hiện đang bị khoá lệnh NSFW, không thể thực hiện tương tác này {self.format_relative_time_vn(self.get_remaining_lock_time(ctx.author.id)['lock_until'])}.")
            return

        member_roles = [role.id for role in ctx.author.roles]

        coefficient = 1
        if self.is_king(member_roles):
            coefficient = 3

        self.record_action("bj", ctx, member, coefficient=coefficient)

        await self._send_embed(
            ctx,
            title="👅 Bú bú",
            description=f"{ctx.author.mention} bú cu {member.mention} 💖",
            gif_url=self.bj_picker.pick(),
            footer=f"Bị {ctx.author.name} bú x{coefficient} lần" if coefficient > 1 else None
        )

    @blowjob.error
    async def blowjob_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Lệnh đang trong thời gian hồi, vui lòng chờ {error.retry_after:.1f} giây nữa.")

    # RIMJOB
    @commands.command(name="rj")
    @commands.cooldown(1, 15, commands.BucketType.user)  # 1 use per 15 seconds per user
    async def rimjob(self, ctx: commands.Context, member: discord.Member):
        if not await self._nsfw_guard(ctx):
            return
        
        if member == ctx.author:
            await ctx.send("Bạn không thể tự liếm lồn mình được đâu 😳")
            return

        if (self.check_if_user_is_locked(ctx.author.id)):
            await ctx.send(f"{member.mention} hiện đang bị khoá lệnh NSFW, không thể thực hiện tương tác này {self.format_relative_time_vn(self.get_remaining_lock_time(ctx.author.id)['lock_until'])}.")
            return

        member_roles = [role.id for role in ctx.author.roles]

        coefficient = 1
        if self.is_king(member_roles):
            coefficient = 3

        self.record_action("rj", ctx, member, coefficient=coefficient)

        await self._send_embed(
            ctx,
            title="🍑 Liếm cái ik~",
            description=f"{ctx.author.mention} liếm lồn {member.mention} 👅💦",
            gif_url=self.rj_picker.pick(),
            footer=f"Bị {ctx.author.name} liếm lồn x{coefficient} lần" if coefficient > 1 else None
        )

    @rimjob.error
    async def rimjob_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Lệnh đang trong thời gian hồi, vui lòng chờ {error.retry_after:.1f} giây nữa.")

    # HANDJOB
    @commands.command(name="hj")
    @commands.cooldown(1, 15, commands.BucketType.user)  # 1 use per 15 seconds per user
    async def handjob(self, ctx: commands.Context, member: discord.Member):
        if not await self._nsfw_guard(ctx):
            return
        
        # ALLOW self-interaction for handjob but comment for future restriction if needed
        # if member == ctx.author:
        #     await ctx.send("Bạn không thể tự sục cặc mình được đâu 😳")
        #     return

        if (self.check_if_user_is_locked(ctx.author.id)):
            await ctx.send(f"{member.mention} hiện đang bị khoá lệnh NSFW, không thể thực hiện tương tác này {self.format_relative_time_vn(self.get_remaining_lock_time(ctx.author.id)['lock_until'])}.")
            return

        member_roles = [role.id for role in ctx.author.roles]

        coefficient = 1
        if self.is_king(member_roles):
            coefficient = 3

        self.record_action("hj", ctx, member, coefficient=coefficient)

        await self._send_embed(
            ctx,
            title="🥰 Sục cho nè~",
            description=f"{ctx.author.mention} sục cho {member.mention} 💦",
            gif_url=self.hj_picker.pick(),
            footer=f"Bị {ctx.author.name} sục x{coefficient} lần" if coefficient > 1 else None
        )
    @handjob.error
    async def handjob_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Lệnh đang trong thời gian hồi, vui lòng chờ {error.retry_after:.1f} giây nữa.")

    # FROTTING
    @commands.command(name="frot")
    @commands.cooldown(1, 15, commands.BucketType.user)  # 1 use per 15 seconds per user
    async def frotting(self, ctx: commands.Context, member: discord.Member):
        if not await self._nsfw_guard(ctx):
            return

        if member == ctx.author:
            await ctx.send("Bạn không thể tự đấu kiếm với mình được đâu 😳")
            return

        if (self.check_if_user_is_locked(ctx.author.id)):
            await ctx.send(f"{member.mention} hiện đang bị khoá lệnh NSFW, không thể thực hiện tương tác này {self.format_relative_time_vn(self.get_remaining_lock_time(ctx.author.id)['lock_until'])}.")
            return

        member_roles = [role.id for role in ctx.author.roles]

        coefficient = 1
        if self.is_king(member_roles):
            coefficient = 3

        self.record_action("frot", ctx, member, coefficient=coefficient)

        await self._send_embed(
            ctx,
            title="🤺 Đấu kiếm nhẹ nhàng nha~",
            description=f"{ctx.author.mention} frot với {member.mention} 🌸",
            gif_url=self.frot_picker.pick(),
            footer=f"Bị {ctx.author.name} đấu kiếm x{coefficient} lần" if coefficient > 1 else None
        )

    @frotting.error
    async def frotting_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Lệnh đang trong thời gian hồi, vui lòng chờ {error.retry_after:.1f} giây nữa.")

    # FUCKING
    @commands.command(name="fuck")
    @commands.cooldown(1, 15, commands.BucketType.user)  # 1 use per 15 seconds per user
    async def fucking(self, ctx: commands.Context, member: discord.Member):
        if not await self._nsfw_guard(ctx):
            return

        if member == ctx.author:
            await ctx.send("Bạn không thể tự chịch mình được đâu 😳")
            return

        if (self.check_if_user_is_locked(ctx.author.id)):
            await ctx.send(f"{member.mention} hiện đang bị khoá lệnh NSFW, không thể thực hiện tương tác này {self.format_relative_time_vn(self.get_remaining_lock_time(ctx.author.id)['lock_until'])}.")
            return

        member_roles = [role.id for role in ctx.author.roles]

        coefficient = 1
        if self.is_king(member_roles):
            coefficient = 3
            
        self.record_action("fuck", ctx, member, coefficient=coefficient)

        await self._send_embed(
            ctx,
            title="Lên giường thôi 👉🏻👌🏻💦",
            description=f"{ctx.author.mention} chịch {member.mention} 💦",
            gif_url=self.fuck_picker.pick(),
            footer=f"Bị {ctx.author.name} chịch x{coefficient} lần" if coefficient > 1 else None
        )

    @fucking.error
    async def fucking_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Lệnh đang trong thời gian hồi, vui lòng chờ {error.retry_after:.1f} giây nữa.")

    # CREAMPIE
    @commands.command(name="cream")
    @commands.cooldown(1, 15, commands.BucketType.user)  # 1 use per 15 seconds per user
    async def creampie(self, ctx: commands.Context, member: discord.Member):
        if not await self._nsfw_guard(ctx):
            return

        if member == ctx.author:
            await ctx.send("Bạn không thể tự xuất trong mình được đâu 😳")
            return

        if (self.check_if_user_is_locked(ctx.author.id)):
            await ctx.send(f"{member.mention} hiện đang bị khoá lệnh NSFW, không thể thực hiện tương tác này {self.format_relative_time_vn(self.get_remaining_lock_time(ctx.author.id)['lock_until'])}.")
            return

        member_roles = [role.id for role in ctx.author.roles]

        coefficient = 1
        if self.is_king(member_roles):
            coefficient = 3

        self.record_action("cream", ctx, member, coefficient=coefficient)

        await self._send_embed(
            ctx,
            title="💦 Aaaahhh~! Em chịu không nổi nữa rồi...",
            description=f"{ctx.author.mention} ra bên trong {member.mention} 💦!",
            gif_url=self.cream_picker.pick(),
            footer=f"Bị {ctx.author.name} xuất trong x{coefficient} lần" if coefficient > 1 else None
        )

    @creampie.error
    async def creampie_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Lệnh đang trong thời gian hồi, vui lòng chờ {error.retry_after:.1f} giây nữa.")

    @commands.command(name="ranknsfw", aliases=["nsfwrank"])
    async def ranknsfw(
        self,
        ctx: commands.Context,
        mode_or_action: str | None = None,
        interaction_type: str | None = None,
    ):
        if not await self._nsfw_guard(ctx):
            return

        nsfw_interactions = ["bj", "rj", "hj", "frot", "fuck", "cream"]

        # text cho NGƯỜI CHỦ ĐỘNG
        action_text_given = {
            "bj": "bú cu",
            "rj": "liếm lồn",
            "hj": "sục cho member khác",
            "frot": "đấu kiếm",
            "fuck": "địt member khác",
            "cream": "xuất trong",
        }

        # text cho NGƯỜI BỊ
        action_text_received = {
            "bj": "được bú cu",
            "rj": "được liếm lồn",
            "hj": "được sục cặc",
            "frot": "được đấu kiếm",
            "fuck": "bị địt",
            "cream": "bị xuất trong",
        }

        # mặc định: người CHỦ ĐỘNG
        mode = "given"

        if mode_or_action == "r":
            mode = "received"
            action = interaction_type
        else:
            action = mode_or_action

        if action not in (nsfw_interactions + [None]):
            await ctx.send(
                "Loại tương tác không hợp lệ.\nVui lòng sử dụng: `bj`, `rj`, `hj`, `frot`, `fuck`, `cream`."
            )
            return

        user_field = "$initMember" if mode == "given" else "$targetMember"

        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1)

        pipeline = [
            {"$match": {"created_at": {"$gte": start_of_month, "$lt": end_of_month}}},
            {"$addFields": {"coefficient": {"$ifNull": ["$coefficient", 1]}}},
            {"$group": {"_id": user_field, "count": {"$sum": "$coefficient"}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]

        if action:
            pipeline.insert(0, {"$match": {"action": action}})
        else:
            pipeline.insert(0, {"$match": {"action": {"$in": nsfw_interactions}}})

        top_users = list(self.db["interactions"].aggregate(pipeline))

        lines = []
        for rank, record in enumerate(top_users, start=1):
            user_id = record["_id"]
            count = record["count"]

            user = self.bot.get_user(user_id)
            name = user.mention if user else f"ID {user_id}"

            if mode == "given":
                if action:
                    text = f"{count} lần {action_text_given[action]}."
                else:
                    text = f"{count} lần chơi người khác."
            else:
                if action:
                    text = f"{count} lần {action_text_received[action]}."
                else:
                    text = f"{count} lần bị chơi."

            lines.append(f"**{rank}**. {name} – {text}")

        description = "\n".join(lines) if lines else "Chưa có dữ liệu."

        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year

        if mode == "given":
            title = f"Top 10 con quỷ sex của server tháng {current_month}/{current_year} 😈"
            if action:
                title = f"🏆 Top 10 người {action_text_given[action]} nhiều nhất 💦"
        else:
            title = f"Top 10 noletinhduc tháng {current_month}/{current_year} 👉🏻👌🏻💦"
            if action:
                title = f"🏆 Top 10 người {action_text_received[action]} nhiều nhất 💦"

        embed = discord.Embed(title=title, description=description)
        embed.set_author(name="BXH độ răm", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_image(
            url="https://api-cdn.rule34.xxx//images/1500/85f729598f01b951f528e47b49078414.gif?1585014"
        )
        await ctx.send(embed=embed)

    @commands.command(name="mrank")
    @commands.has_permissions(administrator=True)
    async def monthlyranknsfw(
        self,
        ctx: commands.Context,
        month: int,
        year: int
    ):
        if not await self._nsfw_guard(ctx):
            return
        
        # the logic is similar to ranknsfw but for a specified month and year
        # that need only rank 5 user over all interactions
        # and later, make the embed and send 
        start_of_month = datetime(year, month, 1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1)
        # Pipeline for "given" (người chủ động)
        pipeline_given = [
            {"$match": {"created_at": {"$gte": start_of_month, "$lt": end_of_month}}},
            {"$addFields": {"coefficient": {"$ifNull": ["$coefficient", 1]}}},
            {"$group": {"_id": "$initMember", "count": {"$sum": "$coefficient"}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
        ]

        # Pipeline for "received" (người bị động)
        pipeline_received = [
            {"$match": {"created_at": {"$gte": start_of_month, "$lt": end_of_month}}},
            {"$addFields": {"coefficient": {"$ifNull": ["$coefficient", 1]}}},
            {"$group": {"_id": "$targetMember", "count": {"$sum": "$coefficient"}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
        ]

        top_given = list(self.db["interactions"].aggregate(pipeline_given))
        top_received = list(self.db["interactions"].aggregate(pipeline_received))

        # Build "given" table
        lines_given = []
        for rank, record in enumerate(top_given, start=1):
            user_id = record["_id"]
            count = record["count"]
            user = self.bot.get_user(user_id)
            name = user.mention if user else f"ID {user_id}"
            lines_given.append(f"**{rank}**. {name} – {count} lần")
        
        # Fill remaining positions with blanks
        for rank in range(len(top_given) + 1, 6):
            lines_given.append(f"**{rank}**. —")
        
        # Build "received" table
        lines_received = []
        for rank, record in enumerate(top_received, start=1):
            user_id = record["_id"]
            count = record["count"]
            user = self.bot.get_user(user_id)
            name = user.mention if user else f"ID {user_id}"
            lines_received.append(f"**{rank}**. {name} – {count} lần")

        # Fill remaining positions with blanks
        for rank in range(len(top_received) + 1, 6):
            lines_received.append(f"**{rank}**. —")

        title = f"📊 Tổng kết tháng {month}/{year}"
        embed = discord.Embed(title=title, color=discord.Color.purple())
        embed.set_author(name="BXH độ răm", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(
            name="😈 Top 5 Con Quỷ Sex",
            value="\n".join(lines_given) if lines_given else "Chưa có dữ liệu.",
            inline=False
        )
        
        embed.add_field(
            name="💦 Top 5 Nô Lệ Tình Dục",
            value="\n".join(lines_received) if lines_received else "Chưa có dữ liệu.",
            inline=False
        )

        next_month = month % 12 + 1
        next_year = year if month < 12 else year + 1

        # Add congratulations for new King and Queen
        if top_given:
            king_user_id = top_given[0]["_id"]
            king_user = self.bot.get_user(king_user_id)
            embed.add_field(
            name="👑 Femboy King mới",
            value=f"Chúc mừng {king_user.mention if king_user else f'<@{king_user_id}>'} đã trở thành **Femboy King** tháng {next_month}/{next_year}! 🎉",
            inline=False
            )

        if top_received:
            queen_user_id = top_received[0]["_id"]
            queen_user = self.bot.get_user(queen_user_id)
            embed.add_field(
            name="👑 Femboy Queen mới",
            value=f"Chúc mừng {queen_user.mention if queen_user else f'<@{queen_user_id}>'} đã trở thành **Femboy Queen** tháng {next_month}/{next_year}! 🎉",
            inline=False
            )

        embed.set_image(
            url="https://api-cdn.rule34.xxx//images/1500/85f729598f01b951f528e47b49078414.gif?1585014"
        )
        await ctx.send(embed=embed)

    @monthlyranknsfw.error
    async def monthlyranknsfw_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Bạn cần quyền Quản trị viên để sử dụng lệnh này.")
        elif isinstance(error, commands.BadArgument):
            await ctx.reply("❌ Vui lòng cung cấp tháng và năm hợp lệ. Ví dụ: `!tf mrank 3 2024`")





async def setup(bot: commands.Bot):
    await bot.add_cog(NSFWInteractionCog(bot))
