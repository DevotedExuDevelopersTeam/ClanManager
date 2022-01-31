import discord
from discord.ext import commands, tasks
from asyncio import sleep, TimeoutError
from pickle import load, dump
from datetime import datetime, timedelta
from typing import Optional
from cv2 import imread, cvtColor, COLOR_BGR2GRAY
from skimage.metrics import structural_similarity as compare_ssim
from PIL import Image
from os import remove
from re import search
from cryptography.fernet import Fernet

class PassException(commands.CommandError):
    pass

def savefile(file_name, data):
    with open(file_name, 'wb') as f:
        dump(data, f)

def loadfile(file_name):
    with open(file_name, 'rb') as f:
        return load(f)

def calculate_ssim(file_name) -> float:
    Image.open(file_name).resize(Image.open('profile_example.png').size).save(file_name)

    imageA = imread('profile_example.png')
    imageB = imread(file_name)

    imageA = cvtColor(imageA, COLOR_BGR2GRAY)
    imageB = cvtColor(imageB, COLOR_BGR2GRAY)

    score, diff = compare_ssim(imageA, imageB, full=True)
    return round(score, 2)

# savefile('applications.pkl', {})
# savefile('applicants.pkl', {})
# savefile('timeouts.pkl', {})
# savefile('requests.pkl', {})
applications = loadfile('applications.pkl') #type: dict[int, int] #dict[message_id, user_id]
applicants = loadfile('applicants.pkl') #type: dict[int, datetime]
timeouts = loadfile('timeouts.pkl') #type: dict[int, datetime]
requests = loadfile('requests.pkl') #type: dict[int, list[int]]
print('Files loaded')

bot = commands.Bot(
    command_prefix='!',
    help_command=None,
    intents=discord.Intents.all()
)

d = {
        'psycho': 886539337024561152,
        #'exu': 869836015370637353,
        #'lite': 869836112636567623,
        'dev2': 869836156450271253,
        'dev3': 870559679682584576
    }

@bot.check
async def globalCheck(ctx):
    return ctx.guild.id == 869834203196428351

@tasks.loop(minutes=30)
async def TimeoutKicker():
    for member in timeouts.copy():
        if datetime.now() > timeouts[member]:
            timeouts.pop(member)
            savefile('timeouts.pkl', timeouts)

            user = server.get_member(member)
            if user != None:
                try:
                    try:
                        await user.send(f'You have exceed the timeout and were kicked. Make sure to verify your being in clan or apply next time.')
                    except: pass
                    await user.kick('Timeout')
                except: pass

@bot.listen('on_ready')
async def ReadyController():
    global server

    server = bot.get_guild(869834203196428351) #type: discord.Guild
    TimeoutKicker.start()
    print('Ready')

@bot.listen('on_message')
async def MessagesController(m: discord.Message):
    try:
        if m.channel.guild.id != 869834203196428351: return
    except: return

    if m.channel.id == 869835463559630898 and not m.content.startswith('!verify') and \
not server.get_role(869835746192797707) in m.author.roles and not server.get_role(869835655323193394) in m.author.roles and not m.author.bot:
        await m.delete()
        msg = await m.channel.send(f'{m.author.mention} this channel is __**commands only**__. This guide may help to fix your issue:\n\
1. If you are here to join the clan, press :arrow_left: to get access to applications category\n\
2. This channel is not for talking about anything\n\
3. If you have any clan related issues, go to <#879656632236265482> please\n\
4. If you are confused with anything, go to <#879656706005671956> please')
        await msg.add_reaction('⬅️')
        try:
            await bot.wait_for('reaction_add', check=lambda r, u: r.emoji == '⬅️' and r.message == msg and u == m.author, timeout=30)
            await m.author.remove_roles(server.get_role(869836212393881651))
            await m.author.add_roles(server.get_role(869836255649746955))
        except: pass
        finally:
            await msg.delete()
    elif search(r'\[\d+\]', m.author.display_name) == None and not server.get_role(869835746192797707) in m.author.roles and not server.get_role(869835655323193394) in m.author.roles and not m.author.bot \
and not m.content.startswith('!setid') and m.channel.id == 869837050730397716:
        await m.channel.send(f'{m.author.mention}, you have no set your ID yet! Please use `!setid <your ID>` (without brackets) to do so, or you will keep receiving this notification on every message you send \
and getting muted for 10 seconds.', delete_after=10)
        muted = server.get_role(869880420081213442)
        await m.author.add_roles(muted)
        await sleep(10)
        await m.author.remove_roles(muted)

@bot.listen('on_raw_reaction_add')
async def ReactionsController(payload: discord.RawReactionActionEvent):
    user = server.get_member(payload.user_id) #type: discord.Member
    channel = server.get_channel(payload.channel_id) #type: discord.TextChannel
    if channel == None: return
    message = await channel.fetch_message(payload.message_id) #type: discord.Message

    unverified = server.get_role(869836212393881651) #type: discord.Role
    applicant = server.get_role(869836255649746955) #type: discord.Role
    pending_applicant = server.get_role(880002757485010985) #type: discord.Role

    try:
        if message.channel.guild.id != 869834203196428351: return
    except: return
    
    if message.id == 869850393482522635: #get-started
        await message.remove_reaction(payload.emoji, user)
        if str(payload.emoji) == '1️⃣':
            await user.add_roles(unverified)
        elif str(payload.emoji) == '2️⃣':
            await user.add_roles(applicant)

    elif message.id == 869850397437722695 and str(payload.emoji) == '⬅️': #how-to-join
        await message.remove_reaction(payload.emoji, user)
        await user.add_roles(unverified)
        await user.remove_roles(applicant)

    elif message.id == 869883669970571304 and str(payload.emoji) == '⬅️': #how-to-verify
        await message.remove_reaction(payload.emoji, user)
        await user.add_roles(applicant)
        await user.remove_roles(unverified)

    elif message.id in requests and server.get_role(869835746192797707) in user.roles and not user.bot:
        await message.delete()
        member = server.get_member(requests[message.id][0])
        role = server.get_role(requests[message.id][1])
        requests.pop(message.id)
        savefile('requests.pkl', requests)
        verchannel = server.get_channel(869835463559630898) #type: discord.TextChannel

        await user.remove_roles(unverified)
        if str(payload.emoji) == '✅':
            await verchannel.send(f'{member.mention}, you were successfully verified')
            await sleep(5)
            await member.add_roles(role)
            await member.remove_roles(unverified)
            await verchannel.set_permissions(member, overwrite=None)
        elif str(payload.emoji) == '❌':
            await verchannel.send(f'{member.mention}, your verification request was denied')
            await verchannel.set_permissions(member, overwrite=None)

    elif message.id in applications and server.get_role(869835746192797707) in user.roles and not user.bot:
        await message.clear_reactions()
        member = server.get_member(applications[message.id])
        applications.pop(message.id)
        savefile('applications.pkl', applications)

        if member == None:
            pass
        elif str(payload.emoji) in ('✅', '❌'):
            await channel.set_permissions(user, send_messages=True)
            if str(payload.emoji) == '✅':
                def check(m):
                    return m.author == user and m.content.lower() in ('psycho', 'dev2', 'dev3') and m.channel == channel
                msg = await channel.send(f'{user.mention} please provide the clan you are accepting this person in. Available clans: `psycho`, `dev2`, `dev3`')
                m = await bot.wait_for('message', check=check)
                await msg.delete()
                await m.delete()
                embed = message.embeds[0]
                embed.add_field(name='Status', value=f'Accepted by {user.mention} to `{m.content.lower()}`')
                try:
                    profile_ss = await message.attachments[0].to_file()
                except:
                    profile_ss = None
                await message.delete()
                await server.get_channel(880003459116576778).send(f'{member.mention} your application was approved', embed=embed, file=profile_ss)
                try:
                    await member.send(f'Congratulations, you were accepted to `{m.content.lower()}`. Please contact **{user}** for futher assistance.')
                except: pass
                newchan = await server.create_text_channel(
                    name=f'discussion-{member.name}',
                    category=server.get_channel(880002546305998848),
                    overwrites={
                        server.default_role: discord.PermissionOverwrite(read_messages=False),
                        server.get_role(869835746192797707): discord.PermissionOverwrite(read_messages=True, manage_channels=True),
                        member: discord.PermissionOverwrite(read_messages=True)
                    }
                )
                await channel.send(f'Created a new channel for discussion: {newchan.mention}. Please make sure to delete it after discussion end', delete_after=5)
            elif str(payload.emoji) == '❌':
                def check(m):
                    return m.author == user and m.channel == channel
                msg = await channel.send(f'{user.mention} please provide the reason of denial')
                m = await bot.wait_for('message', check=check)
                await msg.delete()
                await m.delete()
                embed = message.embeds[0]
                embed.add_field(name='Status', value=f'Denied by {user.mention} with the following reason:\n```{m.content}```')
                try:
                    profile_ss = await message.attachments[0].to_file()
                except:
                    profile_ss = None
                await message.delete()
                await server.get_channel(880003667187630130).send(f'{member.mention} your application was denied', embed=embed, file=profile_ss)
                weekday = datetime.now().weekday()
                applicants[member.id] = datetime.now() + timedelta(days=1 if weekday == 0 else 7 - weekday)
                savefile('applicants.pkl', applicants)
                try:
                    await member.send(f'Your clan application was denied, you may try again next war\nReason: `{m.content}`')
                except:
                    pass

            await member.remove_roles(pending_applicant)
            await channel.set_permissions(user, overwrite=None)

    elif message.id == 869850385001644032 and str(payload.emoji) == '📝':
        await message.remove_reaction(payload.emoji, user)
        if user.id in applicants and datetime.now() < applicants[user.id]:
            nextAttempt = (applicants[user.id]-datetime.now()) #type: timedelta
            await channel.send(f'{user.mention}, you cannot apply more often than once per day, or your application was recently denied. \
Try again in **{str(nextAttempt.days)+" day(s) " if nextAttempt.days > 0 else ""}{str(nextAttempt.seconds//3600)+" hours" if nextAttempt.seconds > 3600 else str(nextAttempt.seconds//60)+" minutes"}**', delete_after=5)
        elif pending_applicant in user.roles:
            await channel.send(f'{user.mention}, you already have submitted the application, please have patience.')
        else:
            m = await channel.send(f'{user.mention} please wait, creating a channel...')
            channel = await server.create_text_channel(
                f'apply-{user.name}',
                category=server.get_channel(869834881461530624),
                overwrites={
                    server.default_role: discord.PermissionOverwrite(read_messages=False),
                    user: discord.PermissionOverwrite(read_messages=True, attach_files=True)
                }
            )
            applicants[user.id] = datetime.now() + timedelta(days=1)
            savefile('applicants.pkl', applicants)
            await m.edit(content=f'Channel {channel.mention} was created, head to there please!', delete_after=5)

            questions = {
                'What is your ID?': None,
                'What is your clan rank?': None,
                'What is your average valor?': None,
                'What is your country OR timezone?': None,
                'Do you grind on war start?': None,
                'Please provide screenshot of your pixelgun profile': None}

            decoder = {
                'What is your ID?': 'ID',
                'What is your clan rank?': 'Clan rank',
                'What is your average valor?': 'Average valor',
                'What is your country OR timezone?': 'Country/timezone',
                'Do you grind on war start?': 'War start',
                'Please provide screenshot of your pixelgun profile': 'Profile'}

            answers = {}

            await channel.send(f'{user.mention} please answer the following question')
            for question in questions:
                if question == 'Please provide screenshot of your pixelgun profile':
                    with open('profile_example.png', 'rb') as f:
                        msg = await channel.send(f'{question} as shown on example', file=discord.File(f, filename='example.png'))
                    
                    while 1:
                        try:
                            def check(m):
                                return m.author == user and m.channel == channel and len(m.attachments) > 0
                            m = await bot.wait_for('message', check=check, timeout=600)
                            m1 = await channel.send(f'Please wait, uploading your file...')
                            attachment = m.attachments[0] #type: discord.Attachment
                            await m1.delete()
                            await m.delete()
                            name = f'comparable-{user.id}.png'
                            await attachment.save(name)
                            ssim = calculate_ssim(name)
                            remove(name)
                            if ssim > 0.4:
                                await msg.delete()
                                questions[question] = await attachment.to_file()
                                break
                            else:
                                await channel.send(f'This is not the valid profile screenshot, please follow the example. If you are sure you attached the right one, please visit <#879657154053832754>')
                                file = await attachment.to_file()
                                await server.get_channel(869892727616192513).send(f'<@664911300769349666> wrong profile screenshot detected with SSIM **{ssim}**', file=file)
                                continue
                        except TimeoutError:
                            await channel.send(f'{user.mention} the response timed out, channel is closing...')
                            applicants.pop(user.id)
                            savefile('applicants.pkl', applicants)
                            await channel.delete()
                            return
                        except discord.HTTPException:
                            try:
                                await m1.delete()
                            except: pass
                            await channel.send(f'Your file is too large, please compress it and try to send again')

                else:
                    msg = await channel.send(question)
                    try:
                        def check(m):
                            return m.author == user and m.channel == channel
                        m = await bot.wait_for('message', check=check, timeout=300)
                        questions[question] = m.content
                        await m.delete()
                        await msg.delete()
                    except TimeoutError:
                        await channel.send(f'{user.mention} the response timed out, channel is closing...')
                        applicants.pop(user.id)
                        savefile('applicants.pkl', applicants)
                        await channel.delete()
                        return
                    
            for question in questions:
                answers[decoder[question]] = questions[question]

            try:
                await user.edit(nick=f'{user.name} [{answers["ID"]}]')
            except:
                try:
                    await user.edit(nick=f'[{answers["ID"]}]')
                except: pass
            await channel.send(f'Thanks, I have received all answers, your application will be posted in <#880170641406439426>')
            await user.remove_roles(applicant)
            await user.add_roles(pending_applicant)
            try:
                timeouts.pop(user.id)
                savefile('timeouts.pkl', timeouts)
            except: pass
            await sleep(5)
            await channel.delete()
            
            embed = discord.Embed(
                color=0x00ff00
            )

            for field in answers:
                if field != 'Profile':
                    embed.add_field(name=field, value=answers[field])

            m = await server.get_channel(880170641406439426).send(f'<@&869835746192797707> new application by {user.mention}', embed=embed, file=answers['Profile'])
            await m.add_reaction('✅')
            await m.add_reaction('❌')
            applications[m.id] = user.id
            savefile('applications.pkl', applications)

@bot.listen('on_member_join')
async def JoinController(member: discord.Member):
    await bot.get_channel(869834769612013568).send(f'{member.mention}, welcome to the **{server.name}**! Please make sure to visit <#869835314267566141> to get access to channels or join a clan, otherwise \
you will be automatically kicked in a day')
    timeouts[member.id] = datetime.now() + timedelta(days=1)
    savefile('requests.pkl', requests)

def only_verify(ctx):
        return ctx.channel.id == 869835463559630898

@bot.command()
@commands.check(only_verify)
async def verify(ctx, clan, id: int):
    clan = clan.lower()
    if not clan in d:
        await ctx.send(f'There\'s no clan named `{clan}`. Available clans: `psycho`, `dev2`, `dev3`')
    elif len(ctx.message.attachments) == 0:
        with open('clan_example.png', 'rb') as f:
            await ctx.send(f'{ctx.author.mention}, please use the command again, but attach the screenshot from inside of the clan, as in example', file=discord.File(f, 'example.png'))
    else:
        try:
            await ctx.author.edit(nick=f'{ctx.author.name} [{id}]')
        except:
            await ctx.author.edit(nick=f'[{id}]')
        await ctx.send(f'Request created, wait for consideration. You will be pinged here')
        try:
            timeouts.pop(ctx.author.id)
            savefile('timeouts.pkl', timeouts)
        except: pass
        await ctx.channel.set_permissions(ctx.author, send_messages=False)
        m = await server.get_channel(869835521449426954).send(f'<@&869835746192797707> new verification request by {ctx.author.mention}:\n\
ID: `{id}`\n\
Requested clan: `{clan}`', file=await ctx.message.attachments[0].to_file())
        await m.add_reaction('✅')
        await m.add_reaction('❌')

        requests[m.id] = [ctx.author.id, d[clan]]
        savefile('requests.pkl', requests)

@bot.command()
async def setid(ctx, user: Optional[discord.Member], id: int):
    if user == None:
        user = ctx.author

    roles_ids = [role.id for role in ctx.author.roles]
    if user != ctx.author and not 869835746192797707 in roles_ids and not 869835655323193394 in roles_ids:
        await ctx.send(f'You don\'t have permission to edit other user\'s IDs')
        
    elif user == ctx.author:
        idt = search(r'\[\d+\]', ctx.author.display_name)
        if idt == None:
            try:
                await ctx.author.edit(nick=f'{ctx.author.name} [{id}]')
            except:
                await ctx.author.edit(nick=f'[{id}]')

            await ctx.send(f'Successfully set your ID')
        else:
            await ctx.send(f'You are already ID verified. If you are not, try removing `[` and `]` from your name or ask an admin/officer to verify you manually')

    else:
        idt = search(r'\[\d+\]', user.display_name)
        if idt == None:
            try:
                await user.edit(nick=f'{user.name} [{id}]')
            except:
                await user.edit(nick=f'[{id}]')
        else:
            await user.edit(nick=user.display_name.replace(idt.group(), f'[{id}]'))

        await ctx.send(f'Set the ID for {user.mention}')

@bot.command()
async def nickme(ctx, *, newnick):
    idt = search(r'\[\d+\]', ctx.author.display_name)
    if idt == None:
        await ctx.author.edit(nick=newnick)
        await ctx.send(f'Successfully set your new nick')
    else:
        try:
            await ctx.author.edit(nick=f'{newnick} {idt.group()}')
            await ctx.send(f'Successfully set your new nick')
        except:
            await ctx.send(f'This nickname is too long, try another one')

@bot.command(aliases=['ac'])
@commands.has_any_role('Officer', 'Admin')
async def addclan(ctx, user: discord.Member, clan):
    clan = clan.lower()
    if not clan in d:
        await ctx.send(f'There\'s no clan named `{clan}`. Available clans: `psycho`, `dev2`, `dev3`')
    else:
        await user.add_roles(server.get_role(d[clan]))
        await ctx.send(f'Successfully added `{clan}` role to {user.mention}')

@bot.command(aliases=['rc'])
@commands.has_any_role('Officer', 'Admin')
async def removeclan(ctx, user: discord.Member, clan):
    clan = clan.lower()
    if not clan in d:
        await ctx.send(f'There\'s no clan named `{clan}`. Available clans: `psycho`, `dev2`, `dev3`')
    else:
        await user.remove_roles(server.get_role(d[clan]))
        await ctx.send(f'Successfully removed `{clan}` role from {user.mention}')

@bot.command()
@commands.has_any_role('Officer', 'Admin')
async def close(ctx):
    if ctx.channel.name.startswith('discussion-'):
        await ctx.channel.delete()
    else:
        await ctx.send(f'This channel is not a discussion channel and cannot be deleted')

@bot.command()
@commands.has_role('Admin')
async def allow(ctx, user: discord.User):
    if user.id in timeouts:
        timeouts.pop(user.id)
        savefile('timeouts.pkl', timeouts)
        await ctx.send(f'Allowed {user.mention} to stay here without verification required')
    else:
        await ctx.send(f'That user is not restricted')

@bot.command(aliases=['p'])
@commands.has_role('Admin')
async def purge(ctx, channel: Optional[discord.TextChannel], user: Optional[discord.User], amount: int):
    purged = 0
    if channel == None: channel = ctx.channel
    await ctx.message.delete()
    await ctx.send(f'Please wait, purging the messages...')
    if amount < 0: amount = -amount
    if amount > 1000: amount = 1000
    if user == None:
        p = await channel.purge(limit=amount, check=lambda m: not m.pinned)
        purged = len(p)
    else:
        if amount > 100: amount = 100
        amount += 1
        todel = []
        async for m in channel.history(limit=200):
            if m.author == user and not m.pinned:
                todel.append(m)
                amount -= 1
            if amount <= 0:
                break

        purged = len(todel)
        await channel.delete_messages(todel)

    await ctx.send(f'Successfully purged **{purged}** messages from {channel.mention}', delete_after=3)

@bot.command(aliases=['pt'])
@commands.has_role('Admin')
async def purgetill(ctx, *, user: discord.User = None):
    await ctx.message.delete()
    if ctx.message.reference == None:
        await ctx.send(f'Please reply to a message')
    else:
        msg = await ctx.send(f'Please wait, purging the messages...')
        purged = 0
        if user == None:
            p = await ctx.channel.purge(limit=1000, after=ctx.message.reference.resolved.created_at, check=lambda m: not m.pinned)
            purged = len(p)
        else:
            p = await ctx.channel.purge(limit=1000, after=ctx.message.reference.resolved.created_at, check=lambda m: not m.pinned and m.author == user)
            purged = len(p)
            try:
                await msg.delete()
            except: pass

        await ctx.send(f'Successfully purged **{purged}** messages from {ctx.channel.mention}', delete_after=3)

@bot.command(aliases=['topsycho', 'changeclan'])
async def migrate(ctx, *, member: discord.Member = None):
    if member != None and not server.get_role(869835746192797707) in member.roles:
        raise commands.MissingRole('Officer')
    if member == None: member = ctx.author
    if server.get_role(d['psycho']) in member.roles:
        await ctx.send(f'{member.mention} is already transferred')
        return

    await member.remove_roles(*(server.get_role(869836015370637353), server.get_role(869836112636567623)))
    await member.add_roles(server.get_role(d['psycho']))
    await ctx.send(f'Successfully transferred {member.mention} to psychotic')

@bot.command()
@commands.is_owner()
async def getmsgcontent(ctx, channel: Optional[discord.TextChannel], msg_id: int):
    if channel == None:
        channel = ctx.channel

    try:
        m = await channel.fetch_message(msg_id)
        await ctx.send(f'```{m.content}```')
    except:
        await ctx.send(f'Couldn\'t fetch that message')

@bot.command()
@commands.is_owner()
async def edit(ctx, channel: Optional[discord.TextChannel], msg_id: int, *, newcontent):
    if channel == None:
        channel = ctx.channel

    try:
        m = await channel.fetch_message(msg_id)
        await m.edit(content=newcontent)
        await ctx.send(f'Edited message successfully')
    except:
        await ctx.send(f'Couldn\'t fetch that message')

@bot.command(name='exec')
@commands.is_owner()
async def _exec(ctx, *, code):
    try:
        exec(code)
        await ctx.send(f'Code executed')
    except Exception as e:
        await ctx.send(f'Code was not execuded because the following error occured:\n```{e}```')

@bot.command(name='eval')
@commands.is_owner()
async def _eval(ctx, *, code):
    try:
        r = eval(code)
        await ctx.send(f'Code evaluated:\n```{r}```')
    except Exception as e:
        await ctx.send(f'Code was not execuded because the following error occured:\n```{e}```')

with open('key.key', 'rb') as kf, open('token.crypt', 'rb') as tf:
    bot.run(Fernet(kf.read()).decrypt(tf.read()).decode())