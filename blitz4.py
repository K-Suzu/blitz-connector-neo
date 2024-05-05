from discord.ext import commands
import discord
from discord import app_commands
import wargaming
import datetime 
from google.cloud import bigquery
from google.cloud import storage
from google.cloud import pubsub_v1
from google.oauth2 import service_account
import warnings
import six
import asyncio
import bigframes.pandas as bpd
import pandas as pd

warnings.simplefilter("always", category=PendingDeprecationWarning) 
warnings.simplefilter("always", category=DeprecationWarning) 
wotb = wargaming.WoTB('id', region='asia', language='en')
key_path = "json pass"
google_credentials = service_account.Credentials.from_service_account_file(key_path, scopes=['https://www.googleapis.com/auth/cloud-platform'])
query ='SELECT * FROM `table` order by id ASC'

id_count = 0

intents = discord.Intents.default()
intents.members = True 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
gbq_client = bigquery.Client()
gcs_client = storage.Client()
bucket = gcs_client.bucket('appspot.com')
blob = bucket.blob('wwn_public.csv')
bpd.options.bigquery.project = 'project'
bpd.options.bigquery.location = "us-west1"
    

class Blitz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Successfully loaded : PostForum')
        await self.bot.tree.sync(guild=discord.Object(477666728646672385))
        print("sync")

    async def blitz_connection(author_ign):
        player_data = wotb.account.list(search = author_ign)
        if player_data:
            await client.get_channel(701429114128695357).send(f"IGN検索中…")
        else:
            return

        author_ign = player_data[0]["nickname"]
        user_id = player_data[0]["account_id"]
        player_clan = wotb.clans.accountinfo(account_id = user_id)

        if player_clan[user_id]["clan_id"]:    
            clan_p:int = player_clan[user_id]["clan_id"]
            clan_detail = wotb.clans.info(clan_id = clan_p)
            clan_tag = clan_detail[clan_p]["tag"]
        else:
            clan_p = 0
            clan_tag = None
        
        return author_ign, user_id, clan_p, clan_tag


    @commands.hybrid_command(name = "bcn_add", with_app_command = True, description ="データベースにユーザーデータを登録します")
    @app_commands.guilds(discord.Object(id = 477666728646672385))
    async def add(self,ctx,author_ign:str):
        await ctx.send(f"IGN:{author_ign}を登録します")
        guild = ctx.guild
        member = ctx.author
        table_id = 'table'
        df = bpd.read_gbq(table_id, use_cache=False)

        if (ctx.channel.id != 701429114128695357):
            await ctx.send(f"このチャンネルには送信できません。")
            return

        d_id = member.id
        serach_id = df[df['discord_id'] == d_id]

        if (serach_id.empty):
            pass
        else:
            embed=discord.Embed(title=f'同一ID登録エラー')
            embed.description = "同一アカウントでの再登録はできません。"
            embed.color = discord.Colour.red()
            await ctx.send(embed=embed)
            return

        player_data = wotb.account.list(search = author_ign)
            
        if player_data:
            await ctx.send(f"IGN検索中…")
        else:
            return

        author_ign = player_data[0]["nickname"]
        user_id = player_data[0]["account_id"]
        player_clan = wotb.clans.accountinfo(account_id = user_id)

        if player_clan[user_id]["clan_id"]:    
            clan_p:int = player_clan[user_id]["clan_id"]
            clan_detail = wotb.clans.info(clan_id = clan_p)
            clan_tag = clan_detail[clan_p]["tag"]
        else:
            clan_p = 0
            clan_tag = None
        
        if(user_id == None):
            embed=discord.Embed(title=f'IGN検索エラー')
            embed.description = "IGNが見つかりませんでした"
            embed.color = discord.Colour.red()
            await ctx.send(embed=embed)
            return


        embed=discord.Embed(title=f'WoTBlitzアカウントデータ')
        embed.add_field(name='◇IGN', value=author_ign, inline=True)
        embed.add_field(name='◇クランタグ', value=clan_tag, inline=True)
        embed.color = discord.Color.blue()
        await ctx.send(embed=embed)
        async with ctx.channel.typing():

            date_now = datetime.datetime.now()
            df_sort = df.sort_values('id')
            pick_id = df_sort.iloc[-1]['id']
            if pick_id is None:
                id_count = 1
            else:
                id_count = pick_id
                id_count += 1
            
            df_add = bpd.DataFrame({'id':[id_count],
                                    'ign':[author_ign],
                                    'wargaming_id':[user_id],
                                    'clan':[clan_tag],
                                    'discord_name':[member.name],
                                    'discord_id':[member.id],
                                    'discord_nick':[member.nick],
                                    'date':[date_now]})
            df_added = bpd.concat([df_sort, df_add])

            df_added.to_gbq('table', if_exists='replace')

            guild = ctx.guild
            role_wwn_group = guild.get_role(688932130742337539)
            role_visitor = guild.get_role(688986060612698142)
            role_wwne = guild.get_role(693783330218442792)
            role_wwna = guild.get_role(703761772653445290)
            role_wwn = guild.get_role(945897222313226240)
            role_wwn2 = guild.get_role(945897305322696725)
            role_wwn3 = guild.get_role(945897438105976894)
            role_wwn4 = guild.get_role(945897551205396491)
            role_ign = guild.get_role(828124281577275392)
            role_sheri = guild.get_role(995583015113736192)
            #パブリック鯖

            await member.remove_roles(role_wwn)
            await member.remove_roles(role_wwn2)
            await member.remove_roles(role_wwn3)
            await member.remove_roles(role_wwn4)
            await member.remove_roles(role_wwne)
            await member.remove_roles(role_wwna)
            await member.remove_roles(role_wwn_group)
            await member.remove_roles(role_ign)
            await member.add_roles(role_visitor)

            if clan_p == 1845:
                await member.add_roles(role_wwn)
                await member.add_roles(role_wwn_group)
            elif clan_p == 6800:
                await member.add_roles(role_wwn2)
                await member.add_roles(role_wwn_group)
            elif clan_p == 29274:
                await member.add_roles(role_wwn3)
                await member.add_roles(role_wwn_group)
            elif clan_p == 44817:
                await member.add_roles(role_wwn4)
                await member.add_roles(role_wwn_group)
            elif clan_p == 34796:
                await member.add_roles(role_wwna)
                await member.add_roles(role_wwn_group)
            elif clan_p == 16297:
                await member.add_roles(role_wwne)
                await member.add_roles(role_wwn_group)
            else:
                await member.add_roles(role_visitor)

        await ctx.send(f"ロールを付与しました。")
        await ctx.send(f"IGN: {author_ign}を登録しました")

    @commands.hybrid_command(name = "bcn_update", with_app_command = True, description ="データベースのユーザーデータを更新します")
    @app_commands.guilds(discord.Object(id = 477666728646672385))
    async def update(self,ctx):
        await ctx.send(f"登録情報を更新します")
        async with ctx.channel.typing():
            member = ctx.author
            d_id = member.id
            
            table_id = 'table'
            df = bpd.read_gbq(table_id, use_cache=False)
            update_user = df[df['discord_id'] == d_id]

            if not update_user.empty:
                pass
            else:
                embed=discord.Embed(title=f'ID検索エラー')
                embed.description = "このアカウントは登録されていません。"
                embed.color = discord.Colour.red()
                await ctx.send(embed=embed)
                return
            
            author_ign = update_user.iloc[0, 1]

            player_data = wotb.account.list(search = author_ign)
            if player_data:
                await ctx.send(f"IGN検索中…")
            else:
                await ctx.send("IGNが見つかりませんでした")
                return

            author_ign = player_data[0]["nickname"]
            user_id = player_data[0]["account_id"]
            player_clan = wotb.clans.accountinfo(account_id = user_id)

            if player_clan[user_id]["clan_id"]:    
                clan_p:int = player_clan[user_id]["clan_id"]
                clan_detail = wotb.clans.info(clan_id = clan_p)
                clan_tag = clan_detail[clan_p]["tag"]
            else:
                clan_p = 0
                clan_tag = None        

        embed=discord.Embed(title=f'WoTBlitzアカウントデータ')
        embed.add_field(name='◇IGN', value=author_ign, inline=True)
        embed.add_field(name='◇クランタグ', value=clan_tag, inline=True)
        embed.color = discord.Color.blue()
        await ctx.send(embed=embed)

        async with ctx.channel.typing():
            update_user.iloc[0]['ign'] = author_ign
            update_user.iloc[0]['wargaming_id'] = user_id
            update_user.iloc[0]['clan'] = clan_tag
            update_user.iloc[0]['discord_name'] = member.name
            update_user.iloc[0]['discord_id'] = d_id
            update_user.iloc[0]['disccord_nickname'] = member.nick

            df_removed = df[df['discord_id'] != d_id]
            df_added = bpd.concat([df_removed, update_user])

            df_sort = df_added.sort_values('id')
            df_sort.to_gbq('table', if_exists='replace')
            
            guild = ctx.guild
            role_wwn_group = guild.get_role(688932130742337539)
            role_visitor = guild.get_role(688986060612698142)
            role_wwne = guild.get_role(693783330218442792)
            role_wwna = guild.get_role(703761772653445290)
            role_wwn = guild.get_role(945897222313226240)
            role_wwn2 = guild.get_role(945897305322696725)
            role_wwn3 = guild.get_role(945897438105976894)
            role_wwn4 = guild.get_role(945897551205396491)
            role_ign = guild.get_role(828124281577275392)
            #パブリック鯖

            await member.remove_roles(role_wwn)
            await member.remove_roles(role_wwn2)
            await member.remove_roles(role_wwn3)
            await member.remove_roles(role_wwn4)
            await member.remove_roles(role_wwne)
            await member.remove_roles(role_wwna)
            await member.remove_roles(role_wwn_group)
            await member.remove_roles(role_ign)
            await member.add_roles(role_visitor)

            if clan_p == 1845:
                await member.add_roles(role_wwn)
                await member.add_roles(role_wwn_group)
            elif clan_p == 6800:
                await member.add_roles(role_wwn2)
                await member.add_roles(role_wwn_group)
            elif clan_p == 29274:
                await member.add_roles(role_wwn3)
                await member.add_roles(role_wwn_group)
            elif clan_p == 44817:
                await member.add_roles(role_wwn4)
                await member.add_roles(role_wwn_group)
            elif clan_p == 34796:
                await member.add_roles(role_wwna)
                await member.add_roles(role_wwn_group)
            elif clan_p == 16297:
                await member.add_roles(role_wwne)
                await member.add_roles(role_wwn_group)
            else:
                await member.add_roles(role_visitor)

        await ctx.send(f"ロールを付与しました。")

        await ctx.send(f"{author_ign}を更新しました")

    @commands.hybrid_command(name = "bcn_update_all", with_app_command = True, description ="update all")
    @app_commands.guilds(discord.Object(id = 477666728646672385))
    @discord.ext.commands.has_guild_permissions(administrator = True)
    async def update_all(self,ctx):
        guild = ctx.guild
        await ctx.send("全ユーザーデータを確認します")

        table_id = 'table'
        df = bpd.read_gbq(table_id, use_cache=False)
        df_sort = df.sort_values('id')
        pick_id = df_sort.iloc[-1,0]
        print(pick_id)
        
        for count in range(pick_id):
            print(count)
            update_user = df_sort[df_sort['id'] == count]

            if (update_user.empty):
                continue
            
            update_id = update_user.iat[0,2]
            player_data = wotb.account.info(account_id = update_id)
            if (player_data[update_id] != None):
                author_ign = player_data[update_id]["nickname"],
                player_clan = wotb.clans.accountinfo(account_id = update_id)

                if player_clan[update_id]["clan_id"]:    
                    clan_p:int = player_clan[update_id]["clan_id"]
                    clan_detail = wotb.clans.info(clan_id = clan_p)
                    clan_tag = clan_detail[clan_p]["tag"]
                else:
                    clan_p = 0
                    clan_tag = None
                        

                member = guild.get_member(update_user.iat[0,5])
                if (member == None):
                    df_sort = df_sort[df_sort['ign'] != author_ign]
                    await ctx.send(f"{author_ign}：サーバーにいないため削除しました")
                    continue

                if (update_user.iat[0, 1] == author_ign and update_user.iat[0, 3] == clan_tag and update_user.iat[0, 4] == member.name and update_user.iat[0, 6] == member.nick):
                    continue
                
                update_user.iat[0, 1] = author_ign
                update_user.iat[0, 3] = clan_tag
                update_user.iat[0, 4] = member.name
                update_user.iat[0, 6] = member.nick
                

                role_wwn_group = guild.get_role(688932130742337539)
                role_visitor = guild.get_role(688986060612698142)
                role_wwne = guild.get_role(693783330218442792)
                role_wwna = guild.get_role(703761772653445290)
                role_wwn = guild.get_role(945897222313226240)
                role_wwn2 = guild.get_role(945897305322696725)
                role_wwn3 = guild.get_role(945897438105976894)
                role_wwn4 = guild.get_role(945897551205396491)
                role_ign = guild.get_role(828124281577275392)
                #パブリック鯖

                await member.remove_roles(role_wwn)
                await member.remove_roles(role_wwn2)
                await member.remove_roles(role_wwn3)
                await member.remove_roles(role_wwn4)
                await member.remove_roles(role_wwne)
                await member.remove_roles(role_wwna)
                await member.remove_roles(role_wwn_group)
                await member.remove_roles(role_ign)
                await member.add_roles(role_visitor)

                if clan_p == 1845:
                    await member.add_roles(role_wwn)
                    await member.add_roles(role_wwn_group)
                elif clan_p == 6800:
                    await member.add_roles(role_wwn2)
                    await member.add_roles(role_wwn_group)
                elif clan_p == 29274:
                    await member.add_roles(role_wwn3)
                    await member.add_roles(role_wwn_group)
                elif clan_p == 44817:
                    await member.add_roles(role_wwn4)
                    await member.add_roles(role_wwn_group)
                elif clan_p == 34796:
                    await member.add_roles(role_wwna)
                    await member.add_roles(role_wwn_group)
                elif clan_p == 16297:
                    await member.add_roles(role_wwne)
                    await member.add_roles(role_wwn_group)
                else:
                    await member.add_roles(role_visitor)


            else:
                df_sort = df_sort[df_sort['id'] != update_id]
                await ctx.send(f"{author_ign}：アカウントが見つからないため削除しました")
                continue

            await ctx.send(f"{author_ign}を更新しました")

            if count % 50 == 0:
                df_sort.to_gbq('table', if_exists='replace')

        df_sort.to_gbq('table', if_exists='replace')
        await ctx.send(f"全データ更新完了")
        

    @commands.hybrid_command(name = "bcn_delete", with_app_command = True, description ="データベースのユーザーデータを削除します")
    @app_commands.guilds(discord.Object(id = 477666728646672385))
    async def delete(self,ctx):
        await ctx.send("ユーザーデータを削除します")
        async with ctx.channel.typing():
            member = ctx.author
            d_id = member.id

            table_id = 'table'
            df = bpd.read_gbq(table_id, use_cache=False)
            df_sorted = df.sort_values('id')
            filtered_df = df_sorted[df_sorted['discord_id'] != d_id]

            guild = ctx.guild
            role_wwn_group = guild.get_role(688932130742337539)
            role_visitor = guild.get_role(688986060612698142)
            role_wwne = guild.get_role(693783330218442792)
            role_wwna = guild.get_role(703761772653445290)
            role_wwn = guild.get_role(945897222313226240)
            role_wwn2 = guild.get_role(945897305322696725)
            role_wwn3 = guild.get_role(945897438105976894)
            role_wwn4 = guild.get_role(945897551205396491)
            role_ign = guild.get_role(828124281577275392)
            #パブリック鯖

            await member.remove_roles(role_wwn)
            await member.remove_roles(role_wwn2)
            await member.remove_roles(role_wwn3)
            await member.remove_roles(role_wwn4)
            await member.remove_roles(role_wwne)
            await member.remove_roles(role_wwna)
            await member.remove_roles(role_wwn_group)
            await member.remove_roles(role_visitor)
            await member.add_roles(role_ign)

            filtered_df.to_gbq('table', if_exists='replace')
            await ctx.send(f"{member.name}の登録データを削除しました")

    @commands.hybrid_command(name = "bcn_command_help", with_app_command = True, description ="ヘルプ")
    @app_commands.guilds(discord.Object(id = 477666728646672385))
    async def command_help(self,ctx):
        embed=discord.Embed(title=f'コマンド一覧')
        embed.add_field(name="/bcn_add IGN", value="IGNを登録します。\n例) /bcn_add Azumina373", inline=False)
        embed.add_field(name="/bcn_update", value="登録されている情報を更新します。\nIGNは必要ありません",inline=False)
        embed.add_field(name="/bcn_delete", value="登録した自分のデータを削除します。\nロールも消えます。\nIGNは必要ありません",inline=False)
        embed.color = discord.Colour.blue()
        await ctx.send(embed=embed)

    @commands.hybrid_command(name = "bcn_export", with_app_command = True, description ="export")
    @app_commands.guilds(discord.Object(id = 477666728646672385))
    @discord.ext.commands.has_guild_permissions(administrator = True)
    async def export(self,ctx):
        if (ctx.channel.id != 477671088751378492):
            await ctx.send(f"このチャンネルには送信できません。")
            return
        
        guild = ctx.guild
        df = gbq_client.query(query).to_dataframe()
        df['wargaming_id'] = df['wargaming_id'].astype(str)
        df['discord_id'] = df['discord_id'].astype(str)

        for num in range(len(df)):
            num_count = num - 1
            wgid_sell = df.iat[num_count, 2]
            d_id_sell = df.iat[num_count, 5]
            quote_wgid = '\"' + wgid_sell + '\"'
            quote_d_id = '\"' + d_id_sell + '\"'
            df.iat[num_count, 2] = quote_wgid
            df.iat[num_count, 5] = quote_d_id
            #IDのテキスト化

        df.to_excel('wwn_public.xlsx', index=False)
        await ctx.send(file=discord.File(fp="wwn_public.xlsx"))

    @commands.hybrid_command(name = "wwn_join", with_app_command = True, description ="入隊申請")
    async def join(self,ctx,ign):
        member = ctx.author
        guild = ctx.guild

        if member.get_role(995583015113736192):
            await ctx.send("コマンドを実行する権限がありません")
            ch_id = 948083377322471484
            channel = await self.bot.get_channel(ch_id)

            msg3 = await channel.send("<@&477674487697899523> ブラックリスト登録者が入隊申請しました。")
            msg3_id = msg3.id
            thread_msg = await channel.fetch_message(msg3_id)
            thread_name = "ブラックリスト登録者について"
            thread = await channel.create_thread(name=thread_name, auto_archive_duration=1440, message = thread_msg)
            await thread.send("ブラックリスト登録者が入隊申請しました。サーバー内で不審な行動があった場合速やかに対処してください。")
            return

        def check_reaction(reaction, user):
            user_ok = (user == ctx.author)
            reaction_ok = (reaction.emoji == emoji_thumbs_down or reaction.emoji == emoji_thumbs_up)
            return user_ok and reaction_ok

        def check_reaction2(reaction2, user2):
            return user2 == ctx.author

        player_data = wotb.account.list(search = ign)

        if player_data:
            await ctx.send(f"IGN検索中…")
        else:
            embed=discord.Embed(title=f'IGN検索エラー')
            embed.description = "IGNが見つかりませんでした"
            embed.color = discord.Colour.red()
            await ctx.send(embed=embed)
            return

        author_ign = player_data[0]["nickname"]
        user_id = player_data[0]["account_id"]
        user_info = wotb.account.info(account_id = user_id)
        win = user_info["%d" % user_id]["statistics"]["all"]["wins"]
        battle = user_info["%d" % user_id]["statistics"]["all"]["battles"]
        winrate = win / battle * 100
        winrate = round(winrate, 2)
        winrate_text = str(winrate) + "%"

        if battle >= 6000 and winrate < 50:
            embed=discord.Embed(title=f'入隊条件エラー')
            embed.description = "最低入隊条件は戦闘数6000以上かつ勝率50%以上です"
            embed.color = discord.Colour.red()
            await ctx.send(embed=embed)
            return
        
        if battle < 6000:
            if winrate < 55 or battle < 3000:
                embed=discord.Embed(title=f'入隊条件エラー')
                embed.description = "最低入隊条件は戦闘数3000以上かつ勝率55%以上です"
                embed.color = discord.Colour.red()
                await ctx.send(embed=embed)
                return
        
        embed=discord.Embed(title=f'ユーザーデータ')
        embed.add_field(name='◇IGN', value=author_ign, inline=True)
        embed.add_field(name='◇戦闘数', value=battle, inline=True)
        embed.add_field(name='◇勝率', value=winrate_text, inline=True)
        embed.color = discord.Colour.blue()
        embed.description = "間違いなければ\N{Thumbs Up Sign}を押してください。"
        msg1 = await ctx.send(embed=embed)
        emoji_thumbs_up = "\N{Thumbs Up Sign}"
        emoji_thumbs_down = "\N{Thumbs Down Sign}"
        await msg1.add_reaction(emoji_thumbs_up)
        await msg1.add_reaction(emoji_thumbs_down)
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check_reaction, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("タイムアウトしました。")
            return

        if reaction.emoji == emoji_thumbs_down:
            await ctx.send("もう一度コマンドを入力してください。")
            return

        msg4 = await ctx.send("確認ができたので以下の禁止事項に同意いただければWWNグループに入隊となります。\n\
            \n\
            【禁止事項】\n\
            ・ゲーム内外（lobiなどSNS含む）での相手をけなしたり貶める行為の禁止。\n\
            ・ゲーム内での意図的なケツブロ、AFKなどの妨害行為の禁止。\n\
            ・ゲーム内チャットでの日本語使用の禁止（小隊チャット除く）。\n\
            ・ゲーム内、全チャットでのGG（GoodGame）の禁止。\n\
            （→GGは、勝ち負け関係なく解釈が様々な為）\n\
            ・格差プラトーンの禁止。\n\
            ・登録したアカウントを他者に対し、譲渡及び貸与することの禁止。\n\
            　また、他者アカウントの譲受及び借用することの禁止。\n\
            ・その他、WWNにふさわしくない行為の禁止。\n\
            \n\
            ※上記に違反した場合は、協議に基づき、注意、警告を行います。\n\
            また反省が見られない場合は除隊処分とします。\n\
            \n\
            後日で良いのでこちらも目を通しておいてください。\n\
            \n\
            【WWNクラン規約】\n\
            https://docs.google.com/spreadsheets/d/1hsygHr_MJAOarenUE8a0trtE3CGzZNQYwswdgsKGz1s/pubhtml?gid=1407830882&single=true\n\
            \n\
            同意していただける場合は\N{Thumbs Up Sign}を押してください。")

        emoji_thumbs_up = "\N{Thumbs Up Sign}"
        await msg4.add_reaction(emoji_thumbs_up)
        try:
            reaction2, user2 = await self.bot.wait_for("reaction_add", check=check_reaction2, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send("タイムアウトしました。")
            return

        await ctx.send("同意ありがとうございます。それではWWNに申請を送って、承認されて5分ほどしたらIGN登録チャンネルで/bcn_updateコマンドを使用してください。\n\
        WWNが満員の時はWWN2に申請してください。")

        """
        emoji_1 = "<:wwn1:948785967513354250>"
        emoji_2 = "<:wwn2:948786863672528966>"
        emoji_3 = "<:wwn3:948786865639665685>"
        emoji_4 = "<:wwn4:948786863135662121>"
        emoji_e = "<:wwne:948786920761208892>"
        emoji_old ="<:wwn_old:949546350574444554>"

        embed=discord.Embed(title=f'希望クラン')
        embed.description = "所属したいクランのリアクションを押してください。\n"
        embed.add_field(name='WWN', value='<:wwn1:948785967513354250>')
        embed.add_field(name='WWN2', value='<:wwn2:948786863672528966>')
        embed.add_field(name='WWN3', value='<:wwn3:948786865639665685>')
        embed.add_field(name='WWN4', value='<:wwn4:948786863135662121>')
        embed.add_field(name='WWN-E', value='<:wwne:948786920761208892>')
        embed.add_field(name='希望なし(司令官が割り振り)', value='<:wwn_old:949546350574444554>')
        embed.color = discord.Colour.green()
        msg2 = await ctx.send(embed=embed)
        await msg2.add_reaction(emoji_1)
        await msg2.add_reaction(emoji_2)
        await msg2.add_reaction(emoji_3)
        await msg2.add_reaction(emoji_4)
        await msg2.add_reaction(emoji_e)
        await msg2.add_reaction(emoji_old)

        try:
            reaction2, user2 = await bot.wait_for("reaction_add", check=check_reaction2, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("タイムアウトしました。")
            return
        


        if reaction2.emoji == emoji_1:
            clan = ("WwN")
        elif reaction2.emoji == emoji_2:
            clan = ("WWN2")
        elif reaction2.emoji == emoji_3:
            clan = ("WWN3")
        elif reaction2.emoji == emoji_4:
            clan = ("WWN4")
        elif reaction2.emoji == emoji_e:
            clan = ("WWN-E")
        else:
            clan = ("希望なし")
        """

        ch_id = 948083377322471484
        channel = self.bot.get_channel(ch_id)

        msg3 = await channel.send("<@&477674487697899523> 入隊申請が来ました")
        msg3_id = msg3.id
        thread_msg = await channel.fetch_message(msg3_id)
        thread_name = author_ign + "さん入隊手続き"
        thread = await channel.create_thread(name=thread_name, auto_archive_duration=1440, message = thread_msg)
        await thread.send("入隊希望者が規約同意しました。クラン側の承認をお願いします。承認したらリアクションを押してください")

        

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.errors.BadArgument):
            await ctx.send(" パラメーターの形式が違います")
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(" パラメーターの数が足りません")


    @commands.is_owner()
    @commands.hybrid_command(name = "bcn_reload", with_app_command = True, description ="リロード")
    async def reload(self, ctx, module_name):
        await ctx.send(f" モジュール{module_name} の再読み込みを開始します。")
        try:
            self.bot.reload_extension(module_name)
            await ctx.send(f" モジュール{module_name} の再読み込みを終了しました。")
        except (commands.errors.ExtensionNotLoaded, commands.errors.ExtensionNotFound,commands.errors.NoEntryPointError, commands.errors.ExtensionFailed) as e:
            await ctx.send(f" モジュール{module_name} の再読み込みに失敗しました。理由：{e}")
            return


async def setup(bot):
    await bot.add_cog(Blitz(bot))