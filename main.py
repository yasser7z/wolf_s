import discord
from discord.ext import commands
from config import TOKEN, PREFIX, FOOTER, COLOR_PRIMARY, COLOR_DANGER, MAX_PLAYERS, MIN_PLAYERS
from game_engine import manager, create_lobby_embed, LobbyView

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"[WEREWOLF BOT] متصل كـ {bot.user}")
    print(f"[WEREWOLF BOT] جاهز على السيرفرات: {len(bot.guilds)}")


@bot.command(name='ذئب')
async def start_werewolf(ctx: commands.Context):
    guild_id = ctx.guild.id
    if manager.get_game(guild_id):
        emb = discord.Embed(
            title="❌ اللعبة قائمة بالفعل!",
            description="في لعبة شغالة حالياً في هذا السيرفر. استعمل `-ايقاف` عشان تنهيها.",
            color=COLOR_DANGER
        )
        emb.set_footer(text=FOOTER)
        return await ctx.send(embed=emb)

    game = manager.create_game(guild_id, ctx.channel, ctx.author)
    emb = create_lobby_embed(game)
    view = LobbyView(game)
    msg = await ctx.send(embed=emb, view=view)
    game.lobby_message = msg
    await ctx.message.delete()


@bot.command(name='ايقاف')
async def stop_werewolf(ctx: commands.Context):
    guild_id = ctx.guild.id
    game = manager.get_game(guild_id)
    if not game:
        emb = discord.Embed(
            title="❌ مافي لعبة!",
            description="ما في لعبة شغالة عشان توقفها.",
            color=COLOR_DANGER
        )
        emb.set_footer(text=FOOTER)
        return await ctx.send(embed=emb)

    manager.end_game(guild_id)
    emb = discord.Embed(
        title="⏹️ تم إيقاف اللعبة",
        description="تم إيقاف اللعبة وتصفير الذاكرة بنجاح.",
        color=COLOR_DANGER
    )
    emb.set_footer(text=FOOTER)
    await ctx.send(embed=emb)
    await ctx.message.delete()


@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return
    emb = discord.Embed(
        title="❌ خطأ",
        description=f"```\n{error}\n```",
        color=COLOR_DANGER
    )
    emb.set_footer(text=FOOTER)
    await ctx.send(embed=emb)


if __name__ == '__main__':
    if not TOKEN:
        raise ValueError("❌ DISCORD_TOKEN غير موجود في متغيرات البيئة!")
    bot.run(TOKEN)
