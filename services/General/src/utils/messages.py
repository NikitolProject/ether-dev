import discord

import typing as ty

import pony.orm as orm

from discord.channel import TextChannel
from discord.ext import commands
from discord_components import Button, ButtonStyle

from ..database import Clans, RatingClans, WhiteListUsers, Members

RED_COLOR = 0xf75151
GREEN_COLOR = 0xdec5b
INVISIBLE_COLOR = 0x2f3136
DEFAULT_COLOR = 0x23272A
AVOCADO_COLOR = 0xd3ffb5
BLUE_COLOR = 0x6badf7


async def create_wallet_msg(channel):
    """Создание типового сообщения в клановый <<wallet>> канал"""
    return await channel.send(
        embed=discord.Embed(
            title='This is your personal wallet. And here are 3 things you can do with it:',
            description=
            '''
1. Check balance
2. Send ECT to another DC (Ethers, Nods, Vi1) within the Ether City Network
3. Top Up city's Vault0 to increase your share
            ''',
            colour=INVISIBLE_COLOR
        ),
        components=[
            [
                Button(style=ButtonStyle.blue, label='Balance'),
                Button(style=ButtonStyle.blue, label='Send'),
                Button(style=ButtonStyle.blue, label='Top up'),
                Button(style=ButtonStyle.blue, label='My cities')
            ]
        ])

async def create_statistics_msg(
    channel: TextChannel, exp: int, 
    rating: RatingClans = None, clan: Clans = None
) -> discord.Message:
    """
    Creating a typical message in the clan <<statistics>> channel
    """
    if rating is None:
        return await channel.send(
            embed=discord.Embed(
                title=f'City Stats',
                description=
                f'''
**Rating**: Installed
**City XP**: {exp}
**DC**: 1
**Vault0**: 100 ECT
**Vault1**: 100 ECT
**Vaults**: 200 ECT
**Battles count**: *soon*
**Earned from battles**: *soon*


You can update stats by clicking on the "Refresh" button below.
The first one to update with new details will win 1 ECT. But be careful with multi clicking.
You have 5 attempts before a cooldown.
                        ''',
                colour=INVISIBLE_COLOR
            ),
            components=[
                [
                    Button(style=ButtonStyle.blue, label='Refresh'),
                    Button(style=ButtonStyle.blue, label='Nods'),
                    Button(style=ButtonStyle.blue, label='Cities')
                ]
            ]
        )

    vault0_tokens = 0
    for t in clan.vault0:
        vault0_tokens += int(t.split(':')[1])

    return await channel.send(
        embed=discord.Embed(
            title=f'City Stats',
            description=
            f"""
**Rating**: {rating.clan_rate}
**City XP**: {rating.total_exp}
**DC**: {rating.members_count}
**Vault0**: {vault0_tokens} ECT
**Vault1**: {clan.vault1} ECT
**Vaults**: {vault0_tokens + int(clan.vault1)} ECT
**Battles count**: *soon*
**Earned from battles**: *soon*


You can update stats by clicking on the "Refresh" button below.
The first one to update with new details will win 1 ECT. But be careful with multi clicking.
You have 5 attempts before a cooldown.
            """,
            colour=INVISIBLE_COLOR
        ),
        components=[
            [
                Button(style=ButtonStyle.blue, label='Refresh'),
                Button(style=ButtonStyle.blue, label='Nods'),
                Button(style=ButtonStyle.blue, label='Cities')
            ]
        ]
    )


async def create_system_help_msg(channel: TextChannel, city_setup: ty.Any):
    """
    Creating a typical message in the <<help>> channel
    """
    await channel.send(
        embed=discord.Embed(
            title='Hey! I am the DeClan bot. Your connection provider within the Ether City’s network.',
            description=
            f'''
**What is Ether City and who is the DeClan bot?**
Ether City is the Discord based game made for Discord communities.
Your public server in Discord has its own topic, structure and members.
So why don’t treat that concept as a proper economic unit like a city with its citizens.
All we need is a system or network where different communities could become independent cities.
Ether City is the one. Where Discord servers communicate, trade and compete.
And I, DeClan Bot, will help you to set up and organize everything that’s needed in order to build your city and join the Ether City.

**What exactly can I do in Ether City?**
As a city creator your primary task is to build a city
and attract as many Decentralized
Citizens (DC) as possible. That way your city grows,
becomes more powerful and as a result wealthier. 
For the whitelisted cities this is a great opportunity to become the first
ones to grow your city faster than the others. As well as get familiar with the whole
system right from the beginning.

**How do I build a city?**
Go to {city_setup.mention}.
Read the main message and click on the “City” button. Please note!
Each city is an economic unit that executes different tasks to grow the city's
capitalization. You will need 100 Ether City Tokens (ECT) to finish the establishment.

**What is ECT?**
ECT is the Ether City’s main currency that is used to spend within the system.
During the testing period you won’t be able to withdraw it.
But it’s good to treat this grinding period as the pre-airdrop before the main launch of the game.

**How to get ECT?**
Be active in your city or Ether City server, earn xp, reach new levels, stake ECT in the cities, ask friends to send ECT to your wallet. Here is the additional list:
• Receive any amount of ECT from another player
• Earn 5 ECT it by joining and leveling up on the Ether City info server
• Be active in the #engage and #marketplace channels
• Random airdrop. Randomly selected users receive 1 ECT everyday in each city
• Earn it from the Vault1 daily drop in your cities. The amount depends on your share in the Vault0
• Win 1 ECT in the #stats channel of the city
• Battling other players and trading in the future

**How to keep track of my stats and balance?**
The moment you joined the Ether City info server (discord.gg/ethercity), you got a
personal profile with a wallet.
Go to #wallet channels either in any city you reside in or in the Ether City server.
Your personal profile consists of level and xp.
And your wallet can be used to collect/send ECT within the Ether City network.

**Who are Ethers, Nods and Vi1?**
These are the roles of Ether City’s Decentralized Citizens.
Ethers is the role of a city creator. Just like you
Nods is the role of city’s members.
And Vi1 is the role of everyone. When you joined the Ether City server, you got it instantly.
            ''',
            colour=INVISIBLE_COLOR
        )
    )
    await channel.send(
        embed=discord.Embed(
            description=
            '''
**What are these channels I got on my server?**
These are your city’s channels. Think of them as different departments that communicate with DC:

• Join - registration channel for newcomers and future DCs of your city (visible for everyone in your Discord server)
• Engage - communication channel for DCs of the city
• Marketplace - channel for buying and selling digital items
• Wallet - profile channel to check personal profile and wallet balance
• Stats - information channel to check city’s statistics and leaderboard
• Logs - notification channel for all recent updates
• Help - FAQ channel for everyone including newcomers.
• Voice - default channel for DCs

**How to define a city?**
Each city consists of:

• Serial number. The number city gets after registration. It goes in order from 0000 to infinity.
• Name. Given by the city creator (Discord server’s owner)
• Creator - Ethers. The role of a player who organizes his/her DCs
• Members - Nods. The role of players who bring value to a city they reside in
• Rating among all other cities. It is defined by the overall XP points of city’s Nods
• Vaults. 2 Economical units of your city. It’s created at the same time as the city.
One vault (Vault0) forms the city's capitalization and profit share for each player.
Another one (Vault1) is for collecting profit from everyday activities.
• Channels for various purposes to interact with.
Each channel is a tool that connects players with DeClan Bot.

**Tell me more about XP and Levels**
Each player has own metrics of experience (XP) and level (Lvl)
In order to achieve new levels players must meet a specified amount of XP.
There are different ways to gain XP:

• Get a role of Ethers (500XP)
• Get a role of Nods (100XP)
• Get a role Vi1 (25 XP)
• Be active in the Engage channel in a city or in general-vi1 channel on the Ether City info server. 10 XP for 1/50 messages per 24 hours
• Publish a listing on the city's marketplace. 15 XP for a local listing, 25XP for a global one.

Here is the table of XP player should gain in order to achieve new levels:

• Level 1 = welcome bonus 5 ECT, overall XP = 0
• Level 2 = +7.5 ECT, overall XP = 75
• Level 3 = +15 ECT, overall XP = 225
• Level 4 = +30 ECT, overall XP = 525
• Level 5 = +60 ECT, overall XP = 1125
• Level 6 = +108 ECT, overall XP = 2205
• Level 7 = +194.4 ECT, overall XP = 4149
• Level 8 = +350 ECT, overall XP = 7649
• Level 9 = +630 ECT, overall XP = 13949
• Level 10 = +1134 ECT, overall XP = 25289

Difficulty multiplier from level 10 to level 15 = x1,5
Difficulty multiplier from level 16 to level 25 = x1,4
Difficulty multiplier from level 26 to level 50 = x1,2

            ''',
            colour=INVISIBLE_COLOR
        )
    )
    await channel.send(
        embed=discord.Embed(
            description=
            '''
**What are Vaults?**
Vaults are the primary economical units of each city.
As of now, each city has 2 vaults:
• Vault0. No role can be given inside a city,
unless the player invests his/her ECT into the vault0.
The amount of player’s ECT in the vault0 defines a share that the user has
among other DCs. You can top up a vault0 by registering as Nods or Ethers.
As well as via the custom top up option in the wallet channel of a city you reside in.
• Vault1. Each city generates profit for different activities. Profit is sent to the vault1.
Where it gathers until the execution of daily drop in favor of DCs.
An amount of ECT each player will earn is defined by a personal share in vault0.
City earns ECT from the marketplace listings of another city and by taking place in the top 10 cities leaderboard.

Any player can check the city's vaults in the stats channel.
Top 10 cities daily earnings:
• 1st place - 150 ECT
• 2nd place - 130 ECT
• 3rd place - 110 ECT
• 4th place - 100 ECT
• 5th place - 90 ECT
• 6th place - 90 ECT
• 7th place - 85 ECT
• 8th place - 85 ECT
• 9th place - 80 ECT
• 10th place - 80 ECT

**How does the Marketplace work?**
Each city has its own marketplace. Any DC can post here an NFT with the opensea.io link.
As well as advertise a city across the Ether City network.
And if your NFT collection is verified on OpenSea, you can check its rarity score.

There are 2 ways to advertise an NFT:
• Locally. Inside your city’s marketplace. Free of charge. Publishers gain 15 XP
• Globally. Each marketplace in Ether City network will publish your NFT,
its rarity score (if verified) and a link to your city.
Current price is 15 ECT. Cities split it among each
other according to their overall XP.
Publishers gain 25 XP.


OpenSea verified collections have a checkmark tied to the name.
It will take some time to load rarity scores for new NFT collections.
But eventually it will be added after you show me your NFT for the first time during the publishing.
            ''',
            colour=INVISIBLE_COLOR
        )
    )


async def create_city_help_msg(
    channel: TextChannel, market: TextChannel, 
    wallet: TextChannel, engage: TextChannel, 
    join: TextChannel, stats: TextChannel
) -> None:
    """
    Creating a typical message in the clan <<help>> channel
    """
    await channel.send(
        embed=discord.Embed(
            title='Hey! I am the DeClan bot. Your connection provider within the Ether City’s network.',
            colour=INVISIBLE_COLOR,
            description=
            f'''
**What is Ether City and who is the DeClan bot?**
Ether City is the Discord based game made for Discord communities.
Your public server in Discord has its own topic, structure and members.
So why don’t treat that concept as a proper economic unit like a city with its citizens.
All we need is a system or network where different communities could become independent cities.
Ether City is the one. Where Discord servers communicate, trade and compete.
And I, DeClan Bot, will help you to set up and organize everything that’s needed in order to build your city and join the Ether City.

**What exactly can I do in Ether City?**
Join cities, gain XP, achieve new levels, earn ECT.
That will make your city grow and hence increase the future profits.
Use the marketplace to publish NFTs across all cities and check a rarity score.
As of right now Ether City is in a grinding stage.
Where early adopters test systems of adding value to communities.

**What is ECT?**
ECT is the Ether City’s main currency that is used to spend within the system.
During the testing period you won’t be able to withdraw it.
But it’s good to treat this grinding period as the pre-airdrop before the main launch of the game.

**How to get ECT?**
Be active in your city or Ether City server, earn xp, reach new levels, stake ECT in the cities, ask friends to send ECT to your wallet.
Here is the additional list:
• Receive any amount of ECT from another player
• Earn 5 ECT it by joining and leveling up on the Ether City info server
• Be active in the {engage.mention} and {market.mention} channels
• Random airdrop. Randomly selected users receive 1 ECT everyday in each city
• Earn it from the Vault1 daily drop in your cities. The amount depends on your share in the Vault0
• Win 1 ECT in the {stats.mention} channel of the city
• Battling other players and trading in the future

**How to keep track of my stats and balance?**
Use the {wallet.mention} channel

**Who are Decentralized Citizens (DC)?**
DCs are the Ether City’s players.
All of them have roles:
• Ethers
• Nods
• Vi1

**Who are Ethers?**
Ethers is the role of a city creator.
You can become one just by owning your own Discord Server and installing me (DeClan bot) on it.
During a testing period only whitelisted players have this ability.
In the near future it will be open for everyone.

**Who are Nods?**
Nods is the role of city’s members.
Anyone who joined a city via the {join.mention} channel.

**Who are Vi1?**
Vi1 is the role of everyone.
When you joined the Ether City server (https://discord.com/invite/ethercity), you got it instantly.
            '''
        )
    )
    await channel.send(
        embed=discord.Embed(
            colour=INVISIBLE_COLOR,
            description=
            '''
**Tell me more about XP and Levels**
Each player has own metrics of experience (XP) and level (Lvl)
In order to achieve new levels players must meet a specified amount of XP.
There are different ways to gain XP:
• Get a role of Ethers (500XP)
• Get a role of Nods (100XP)
• Get a role Vi1 (25 XP)
• Be active in the Engage channel in a city or in general-vi1 channel on the Ether City info server. 10 XP for 1/50 messages per 24 hours
• Publish a listing on the city's marketplace. 15 XP for a local listing, 25XP for a global one.

Here is the table of XP player should gain in order to achieve new levels:

• Level 1 = welcome bonus 5 ECT, overall XP = 0
• Level 2 = +7.5 ECT, overall XP = 75
• Level 3 = +15 ECT, overall XP = 225
• Level 4 = +30 ECT, overall XP = 525
• Level 5 = +60 ECT, overall XP = 1125
• Level 6 = +108 ECT, overall XP = 2205
• Level 7 = +194.4 ECT, overall XP = 4149
• Level 8 = +350 ECT, overall XP = 7649
• Level 9 = +630 ECT, overall XP = 13949
• Level 10 = +1134 ECT, overall XP = 25289

Difficulty multiplier from level 10 to level 15 = x1,5
Difficulty multiplier from level 16 to level 25 = x1,4
Difficulty multiplier from level 26 to level 50 = x1,2

**What are Vaults?**
Vaults are the primary economical units of each city.
As of now, each city has 2 vaults:
• Vault0. No role can be given inside a city,
unless the player invests his/her ECT into the vault0.
The amount of player’s ECT in the vault0 defines a share that the user has
among other DCs. You can top up a vault0 by registering as Nods or Ethers.
As well as via the custom top up option in the wallet channel of a city you reside in.
• Vault1. Each city generates profit for different activities. Profit is sent to the vault1.
Where it gathers until the execution of daily drop in favor of DCs.
An amount of ECT each player will earn is defined by a personal share in vault0.
City earns ECT from the marketplace listings of another city and by taking place in the top 10 cities leaderboard.

Any player can check the city's vaults in the stats channel.
Top 10 cities daily earnings:
• 1st place - 150 ECT
• 2nd place - 130 ECT
• 3rd place - 110 ECT
• 4th place - 100 ECT
• 5th place - 90 ECT
• 6th place - 90 ECT
• 7th place - 85 ECT
• 8th place - 85 ECT
• 9th place - 80 ECT
• 10th place - 80 ECT

**How does the Marketplace work?**
Each city has its own marketplace. Any DC can post here an NFT with the opensea.io link.
As well as advertise a city across the Ether City network.
And if your NFT collection is verified on OpenSea, you can check its rarity score.

There are 2 ways to advertise an NFT:
• Locally. Inside your city’s marketplace. Free of charge. Publishers gain 15 XP
• Globally. Each marketplace in Ether City network will publish your NFT,
its rarity score (if verified) and a link to your city.
Current price is 15 ECT.
Cities split it among each other according to their overall XP.
Publishers gain 25 XP.


OpenSea verified collections have a checkmark tied to the name.
It will take some time to load rarity scores for new NFT collections.
But eventually it will be added after you show me your NFT for the first time during the publishing.
            '''
        )
    )


async def create_city_setup_msg(
    ch_city_setup: TextChannel, ch_help: TextChannel
) -> discord.Message:
    """
    Creating a typical message in the <<city-setup>> channel
    """

    emb = discord.Embed(
        title='Build your city',
        description=
        f'''
Welcome to the Ether City Network. 
I am the DeClan Bot. And I am here to help you to build the city in this Discord Server. In order to start you need 2 things:

1. The name of the city
2. 100 ECT to stake in the city's vault

To proceed press the "City" button below.
If you need more details go to {ch_help.mention} channel
        ''',
        color=0x2f3136,
    )

    msg_setup = await ch_city_setup.send(
        embed=emb, 
        components=[
            [
                Button(style=ButtonStyle.green, label='City')
            ]
        ]
    )
    return msg_setup


async def create_marketplace_msg(channel: TextChannel) -> discord.Message:
    """
    Creating a typical message in the clan <<marketplace>> channel
    """
    return await channel.send(
        embed=discord.Embed(
            title='Welcome to the Marketplace.',
            description=
            '''
Here you can post your NFTs from opensea.io. You've got 2 options:

- Post via the "Local" button. Only this city's DC will see it.
- Post via the "Global" button. That way every DC will see your post within Ether City Network. Listing price is 15 ECT. It will be distributed among all cities' Vaults1.

On both of the options you can check a rarity score of your NFT (should be a verified collection on opensea.io)
            ''',
            colour=INVISIBLE_COLOR
        ),
        components=[
            [
                Button(style=ButtonStyle.blue, label='Local'),
                Button(style=ButtonStyle.blue, label='Global')
            ]
        ]
    )


async def create_join_msg(channel: TextChannel, name: str):
    """
    Creating a typical message in the clan <<join>> channel
    """
    return await channel.send(
        embed=discord.Embed(
            title=f'Welcome to {name}!',
            description='''
I am the DeClan bot. And I am here to help you to join the city that was built in this
Discord Server. By joining a city you boost its economy and earn Ether City Tokens.
You can join as many cities as you'd like. All you need is 5 ECT in your Ether City wallet.
To create one go to https://discord.com/invite/ethercity

Then press the "Join" button below and follow the instructions.
            ''',
            colour=INVISIBLE_COLOR,
        ),
        components=[
            [
                Button(style=ButtonStyle.blue, label='Join')
            ]
        ]
    )



async def create_wallet_msg(channel: TextChannel) -> discord.Message:
    """
    Creating a typical message in the clan <<wallet>> channel
    """
    return await channel.send(
        embed=discord.Embed(
            title='This is your personal wallet. And here are 3 things you can do with it:',
            description=
            '''
1. Check balance
2. Send ECT to another DC (Ethers, Nods, Vi1) within the Ether City Network
3. Top Up city's Vault0 to increase your share
            ''',
            colour=INVISIBLE_COLOR
        ),
        components=[
            [
                Button(style=ButtonStyle.blue, label='Balance'),
                Button(style=ButtonStyle.blue, label='Send'),
                Button(style=ButtonStyle.blue, label='Top up'),
                Button(style=ButtonStyle.blue, label='My cities')
            ]
        ])



async def create_system_help_msg(
    channel: discord.TextChannel, city_setup: TextChannel
) -> None:
    """
    Creating a typical message in the <<help>> channel
    """

    await channel.send(
        embed=discord.Embed(
            title='Hey! I am the DeClan bot. Your connection provider within the Ether City’s network.',
            description=
            f'''
**What is Ether City and who is the DeClan bot?**
Ether City is the Discord based game made for Discord communities.
Your public server in Discord has its own topic, structure and members.
So why don’t treat that concept as a proper economic unit like a city with its citizens.
All we need is a system or network where different communities could become independent cities.
Ether City is the one. Where Discord servers communicate, trade and compete.
And I, DeClan Bot, will help you to set up and organize everything that’s needed in order to build your city and join the Ether City.

**What exactly can I do in Ether City?**
As a city creator your primary task is to build a city
and attract as many Decentralized
Citizens (DC) as possible. That way your city grows,
becomes more powerful and as a result wealthier. 
For the whitelisted cities this is a great opportunity to become the first
ones to grow your city faster than the others. As well as get familiar with the whole
system right from the beginning.

**How do I build a city?**
Go to {city_setup.mention}.
Read the main message and click on the “City” button. Please note!
Each city is an economic unit that executes different tasks to grow the city's
capitalization. You will need 100 Ether City Tokens (ECT) to finish the establishment.

**What is ECT?**
ECT is the Ether City’s main currency that is used to spend within the system.
During the testing period you won’t be able to withdraw it.
But it’s good to treat this grinding period as the pre-airdrop before the main launch of the game.

**How to get ECT?**
Be active in your city or Ether City server, earn xp, reach new levels, stake ECT in the cities, ask friends to send ECT to your wallet. Here is the additional list:
• Receive any amount of ECT from another player
• Earn 5 ECT it by joining and leveling up on the Ether City info server
• Be active in the #engage and #marketplace channels
• Random airdrop. Randomly selected users receive 1 ECT everyday in each city
• Earn it from the Vault1 daily drop in your cities. The amount depends on your share in the Vault0
• Win 1 ECT in the #stats channel of the city
• Battling other players and trading in the future

**How to keep track of my stats and balance?**
The moment you joined the Ether City info server (discord.gg/ethercity), you got a
personal profile with a wallet.
Go to #wallet channels either in any city you reside in or in the Ether City server.
Your personal profile consists of level and xp.
And your wallet can be used to collect/send ECT within the Ether City network.

**Who are Ethers, Nods and Vi1?**
These are the roles of Ether City’s Decentralized Citizens.
Ethers is the role of a city creator. Just like you
Nods is the role of city’s members.
And Vi1 is the role of everyone. When you joined the Ether City server, you got it instantly.
            ''',
            colour=INVISIBLE_COLOR
        )
    )
    await channel.send(
        embed=discord.Embed(
            description=
            '''
**What are these channels I got on my server?**
These are your city’s channels. Think of them as different departments that communicate with DC:

• Join - registration channel for newcomers and future DCs of your city (visible for everyone in your Discord server)
• Engage - communication channel for DCs of the city
• Marketplace - channel for buying and selling digital items
• Wallet - profile channel to check personal profile and wallet balance
• Stats - information channel to check city’s statistics and leaderboard
• Logs - notification channel for all recent updates
• Help - FAQ channel for everyone including newcomers.
• Voice - default channel for DCs

**How to define a city?**
Each city consists of:

• Serial number. The number city gets after registration. It goes in order from 0000 to infinity.
• Name. Given by the city creator (Discord server’s owner)
• Creator - Ethers. The role of a player who organizes his/her DCs
• Members - Nods. The role of players who bring value to a city they reside in
• Rating among all other cities. It is defined by the overall XP points of city’s Nods
• Vaults. 2 Economical units of your city. It’s created at the same time as the city.
One vault (Vault0) forms the city's capitalization and profit share for each player.
Another one (Vault1) is for collecting profit from everyday activities.
• Channels for various purposes to interact with.
Each channel is a tool that connects players with DeClan Bot.

**Tell me more about XP and Levels**
Each player has own metrics of experience (XP) and level (Lvl)
In order to achieve new levels players must meet a specified amount of XP.
There are different ways to gain XP:

• Get a role of Ethers (500XP)
• Get a role of Nods (100XP)
• Get a role Vi1 (25 XP)
• Be active in the Engage channel in a city or in general-vi1 channel on the Ether City info server. 10 XP for 1/50 messages per 24 hours
• Publish a listing on the city's marketplace. 15 XP for a local listing, 25XP for a global one.

Here is the table of XP player should gain in order to achieve new levels:

• Level 1 = welcome bonus 5 ECT, overall XP = 0
• Level 2 = +7.5 ECT, overall XP = 75
• Level 3 = +15 ECT, overall XP = 225
• Level 4 = +30 ECT, overall XP = 525
• Level 5 = +60 ECT, overall XP = 1125
• Level 6 = +108 ECT, overall XP = 2205
• Level 7 = +194.4 ECT, overall XP = 4149
• Level 8 = +350 ECT, overall XP = 7649
• Level 9 = +630 ECT, overall XP = 13949
• Level 10 = +1134 ECT, overall XP = 25289

Difficulty multiplier from level 10 to level 15 = x1,5
Difficulty multiplier from level 16 to level 25 = x1,4
Difficulty multiplier from level 26 to level 50 = x1,2

            ''',
            colour=INVISIBLE_COLOR
        )
    )
    await channel.send(
        embed=discord.Embed(
            description=
            '''
**What are Vaults?**
Vaults are the primary economical units of each city.
As of now, each city has 2 vaults:
• Vault0. No role can be given inside a city,
unless the player invests his/her ECT into the vault0.
The amount of player’s ECT in the vault0 defines a share that the user has
among other DCs. You can top up a vault0 by registering as Nods or Ethers.
As well as via the custom top up option in the wallet channel of a city you reside in.
• Vault1. Each city generates profit for different activities. Profit is sent to the vault1.
Where it gathers until the execution of daily drop in favor of DCs.
An amount of ECT each player will earn is defined by a personal share in vault0.
City earns ECT from the marketplace listings of another city and by taking place in the top 10 cities leaderboard.

Any player can check the city's vaults in the stats channel.
Top 10 cities daily earnings:
• 1st place - 150 ECT
• 2nd place - 130 ECT
• 3rd place - 110 ECT
• 4th place - 100 ECT
• 5th place - 90 ECT
• 6th place - 90 ECT
• 7th place - 85 ECT
• 8th place - 85 ECT
• 9th place - 80 ECT
• 10th place - 80 ECT

**How does the Marketplace work?**
Each city has its own marketplace. Any DC can post here an NFT with the opensea.io link.
As well as advertise a city across the Ether City network.
And if your NFT collection is verified on OpenSea, you can check its rarity score.

There are 2 ways to advertise an NFT:
• Locally. Inside your city’s marketplace. Free of charge. Publishers gain 15 XP
• Globally. Each marketplace in Ether City network will publish your NFT,
its rarity score (if verified) and a link to your city.
Current price is 15 ECT. Cities split it among each
other according to their overall XP.
Publishers gain 25 XP.


OpenSea verified collections have a checkmark tied to the name.
It will take some time to load rarity scores for new NFT collections.
But eventually it will be added after you show me your NFT for the first time during the publishing.
            ''',
            colour=INVISIBLE_COLOR
        )
    )


async def add_to_white_list(member: discord.User) -> None:
    """
    A function that implements adding a given id to the whitelist of server owners
    """

    await member.send(
        '''
        **Hey, DC! Congrats on passing to the whitelist.**
You've been granted the access to build one of the first cities of the Ether City network.
Just to be sure that we are on the same page here:

*- City = Discord Server
- DC (Decentralized Citizen) = Ether City member
- DeClan bot = Me*

Please invite me to your server. So I could help you to organize your city. Click here to invite:
https://discord.com/api/oauth2/authorize?client_id=836627971959160923&permissions=8&scope=bot

You will need 100 ECT to build your city. But do not worry I’ve just deposited 300 ECT into your wallet. 

Go to city-setup on your server and click on the “City” button. I will respond in DM, asking for the city name and confirmation. If your DM is closed I won’t be able to reach you. After the confirmation you will have a new category with channels on the server. City’s DCs will interact with these channels to keep your city growing. 

**The city will also receive 2 Vaults after the registration:**

Vault0 represents the city's capitalization. 100 ECT that you used for registration is staked into the Vault0. That makes you a 100% city shareholder. However, anyone who joins your city has to stake 5 ECT into the Vault0. That will decline your share, but eventually grow the city. Which is a good thing. And you can always increase your share in the Vault0 by using the Top Up option in the wallet channel.
Vault1 holds and distributes daily profits your city generates. And the distribution amount of ECT to each player depends on his/her share in the Vault0.
        '''
    )
    await member.send(
        '''
        People who want to join your city should have the Ether City wallet and at least 5 ECT. These things are very easy to get. They just need to join the Ether City Discord server and receive the Vi1 role.

Ether City Sever link: https://discord.gg/ethercity    

**As of right now your main goal would be to grow a city:**

*- Attract as many people as you can or want
- Help your people to gain XP and achieve new levels
- Keep spending, staking and collecting ECT*

You will play one of the main roles in shaping the digital economy of Ether City. At the moment it’s a grinding machine with a very few basic features. But as we move forward, you will see how each one of you becomes an independent and scalable community, designated from Discord or any other platform. With your own ideas, own currency, personal army, automatic marketplace and other “not crazy at all” plans.

The people who defined the idea of Ether City are now gone. They left us with the story and motivation to upgrade digital society. Me, the DeClan bot along with Devs will support Ether City’s development until it’s fully autonomous and decentralized. 

**Thank you for joining us so early. Welcome to the deployment stage, Ethers!  **

Don't forget that we are in the testing period. It will take time to grow and make everything work perfectly
        '''
    )
    with orm.db_session:
        WhiteListUsers(
            id=str(member.id),
            name=member.name,
        )
        user = Members.get(id=str(member.id))
        user.tokens = str(float(user.tokens) + 300.0)
