import os
import json

import asyncio
import datetime

import requests
import discord

from aiohttp import ClientSession

from discord.ext import commands
from discord_components import Button, ButtonStyle

from . import *
from .utils import *
from .database import *
from .utils.messages import *


class Marketplace(BasicCog, name='marketplace'):

    async def send_message_market(
        self: "Marketplace", f_interaction: Interaction, data: dict
    ) -> tuple: 
        """
        Function for sending a message to the marketplace
        """
        slug: str = "-".join(data['asset_contract']["name"].lower().split(' '))

        async with ClientSession() as session:
            async with session.get(
                f"https://api.opensea.io/api/v1/collection/{slug}/stats"
            ) as response:
                if response.status != 200:
                    raise ValueError

                stats = await response.json()

                if len(stats) <= 0:
                    raise ValueError

                await session.close()
            
        with orm.db_session:
            price = False
            price_text = f"\n· Price: **{int(data['orders'][-1]['base_price']) / 1000000000000000000} Ξ**\n" if price else None
            rarity_text = None

            try:
                rarity, do_message = await get_rarity(data)
                await self._log(rarity, do_message)
                if rarity is not None:
                    rarity_text = f"\n· Rarity: **{rarity[0]}/{rarity[1]}(Score {float_round(float(rarity[2]), 2)})**\n"

                if do_message:
                    clan: Clans = Clans.get(channel_marketplace_id=str(f_interaction.channel.id))

                    if clan is not None:
                        channel = self.bot.get_channel(int(clan.channel_logs_id))
                        await send_embed(
                            title='Rarity Score',
                            text=f'{data["collection"]["name"]} is downloading.\n The process will take for approx. 10-15 min',
                            color=BLUE_COLOR,
                            channel=channel
                        )

            except Exception as e:
                await self._error(
                    'send_message_market error: ', e, f_interaction.user.id, 
                    f_interaction.user.name
                )

            emb = discord.Embed(
                title=f"**{data['collection']['name']}{' ☑️' if data['collection']['safelist_request_status'] == 'verified' else ''}**",
                description=f'''
    {f'**{data["name"]}**' if data["name"] is not None else ''}
    {price_text if price and data['orders'][0]['base_price'] != '0' else ''} {rarity_text if rarity_text is not None else ''}
· Floor price: **{stats['stats']['floor_price']} Ξ**

· Items: **{int(data['collection']['stats']['count'])}**

· Owners: **{int(data['collection']['stats']['num_owners'])}**

· Volume: **{float_round(data['collection']['stats']['total_volume'], 1)} Ξ**
                ''',
                colour=GREEN_COLOR
            ).set_image(url=data['image_url']).set_footer(text='Ξther City Network')

            msg = await f_interaction.user.send(
                embed=emb,
                components=[
                    Button(style=ButtonStyle.green, label='Publish'),
                    Button(style=ButtonStyle.red, label='Cancel')
                ]
            )
            return msg, emb

    async def __error_msg(self: "Marketplace", errors: int, f_interaction: Interaction) -> None:
        if errors < 5:
            await send_embed(
                title='Incorrect link!',
                text='Please, reply with a correct link to NFT on opensea.io',
                color=RED_COLOR,
                footer=f'{errors}/5 attempts',
                member=f_interaction.user)
            await self._error(
                'check_link incorrect link', f_interaction.user.id, f_interaction.user.name
            )

    async def _json(self: "Marketplace", data: dict) -> None:
        """
        Function for getting the json from opensea
        """
        print(data)
        with open('opensea.json', 'w') as f:
            json.dump(data, f, indent=4)

    async def check_link(
        self: "Marketplace", f_interaction: Interaction
    ) -> ty.Tuple[ty.Union[None, bool, dict], ty.Union[None, bool, str]]:
        """
        Function to check the suitability of the link for the marketplace
        """
        errors: int = 0

        await send_embed(
            text='Reply with a link to your NFT on opensea.io',
            color=INVISIBLE_COLOR,
            member=f_interaction.user,
            interaction=f_interaction)
        await invisible_respond(f_interaction)

        while errors < 5:
            try:
                message = await self.bot.wait_for(
                    'message', timeout=120,
                    check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private
                )
            except asyncio.TimeoutError:
                await timeout_error(f_interaction.user)
                return None, None

            try:
                link = message.content
                if link.split('/')[2] != 'opensea.io' or link.split('/')[3] != 'assets':
                    raise TypeError

                try:
                    async with ClientSession() as session:
                        async with session.get(
                            f"https://api.opensea.io/api/v1/asset/{str(link.split('/')[4])}/{str(link.split('/')[5])}"
                        ) as response:

                            if response.status != 200:
                                raise ValueError

                            data = await response.json()

                            await self._json(data)

                            if len(data) <= 0:
                                raise ValueError

                            await session.close()
                            return data, link

                except Exception as e:
                    await self._error(
                        'check_link error: ', e, f_interaction.user.id, f_interaction.user.name
                    )

                    errors += 1
                    await self.__error_msg(
                        errors, f_interaction
                    )
                    continue

            except Exception:
                errors += 1
                await self.__error_msg(
                    errors, f_interaction
                )
                continue

        await send_embed(
            text='You exceeded the amount of attempts (5). Please, retry after the 10 min cooldown.',
            color=RED_COLOR,
            member=f_interaction.user
        )
        return False, None

    async def market_local_button(self: "Marketplace", f_interaction: Interaction) -> ty.Union[None, bool]:
        """
        Publishing an ad on the clan marketplace
        """
        with orm.db_session:
            clan: Clans = Clans.get(channel_marketplace_id=str(f_interaction.channel.id))

            if clan is None:
                return None

            dm = await f_interaction.author.create_dm()

            await f_interaction.respond(
                embed=discord.Embed(
                    description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                    color=discord.Colour.dark_blue()
                )
            )

            await self._log(
                'marketplace local used', f_interaction.user.id, 
                f_interaction.user.name, f_interaction.guild.id, 
                f_interaction.guild.name
            )

            data, link = await self.check_link(f_interaction)

            if data is None or not data:
                return None

            elif len(data) > 0:
                msg, emb = await self.send_message_market(f_interaction, data)
                try:
                    msg_interaction = await self.bot.wait_for(
                        'button_click', timeout=120,
                        check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private and m.message == msg
                    )
                except asyncio.TimeoutError:
                    await timeout_error(f_interaction.user)
                    return None

                if msg_interaction.component.label == 'Cancel':
                    await invisible_respond(msg_interaction)
                    await send_embed(
                            text='You have canceled the sending of your NFT.',
                            color=RED_COLOR,
                            member=f_interaction.user
                    )
                    return False

                if msg_interaction.component.label == 'Publish':
                    await invisible_respond(msg_interaction)
                    member: Members = Members.get(
                        id=str(f_interaction.user.id),
                    )
                    print(1)
                    member.exp_rank = str(int(member.exp_rank) + 15)
                    member.total_count_sends_mark_local = "1" if not member.total_count_sends_mark_local else str(int(member.total_count_sends_mark_local) + 1)
                    print(2)

                    try:
                        local_msg = await f_interaction.channel.send(
                            embed=emb,
                            components=[
                                [
                                    Button(style=ButtonStyle.URL, url=link, label='Link'),
                                    Button(style=ButtonStyle.blue, label='Local'),
                                    Button(style=ButtonStyle.blue, label='Global')
                                ]
                            ]
                        )

                        await send_embed(
                            text='Your NFT was published successfully on the city\'s marketplace.\nEarned 15XP\n30 min. cooldown on publishing',
                            color=GREEN_COLOR,
                            member=f_interaction.user)
                        
                        TransactionMain(
                            user_id=str(f_interaction.user.id),
                            to_channel=str(f_interaction.channel.id),
                            msg_id=str(local_msg.id),
                            from_clan=str(clan._id),
                            link=link,
                            date=str(datetime.now()),
                        )

                        await self._log(
                            'send local marketplace: ', f_interaction.user.id,
                             f_interaction.user.name, 'clan: ', clan.token
                        )
                        await self.bot.get_cog('rating').new_lvl(member.id)
                        return True

                    except Exception as e:
                        await self._error(str(e))
                        await send_embed(
                            title='Unexpected Error',
                            text='The marketplace is disconnected. Can\'t publish.',
                            color=RED_COLOR,
                            member=f_interaction.user
                        )
                        return None

    async def __success_send(self: "Marketplace", f_interaction: Interaction, link: str, emb: Embed) -> bool:
        with orm.db_session:
            member: Members = Members.get(
                id=str(f_interaction.user.id),
            )
            member.tokens = str(float(member.tokens) - 15.0)
            member.total_costs_for_mark_global = "15" if not member.total_costs_for_mark_global else str(int(member.total_costs_for_mark_global) + 15)
            member.total_count_sends_mark_local = "1" if not member.total_count_sends_mark_local else str(int(member.total_count_sends_mark_local) + 1)
            member.exp_rank = str(int(member.exp_rank) + 25)
            orm.commit()

            total_exp = 0
            clan_list = []
            msg_list = []
            clan_link = Clans.get(channel_marketplace_id=str(f_interaction.channel.id)).invite_link \
                if f_interaction.guild.id != discord_config['server_main']\
                else discord_config['invite_link_to_main']

            for clan in Clans.select(lambda c: not c.frozen):
                if int(clan.channel_marketplace_id) != f_interaction.channel.id:
                    total_exp += int(clan.total_exp)
            orm.commit()

            for clan in Clans.select(lambda c: not c.frozen):
                try:
                    clan_pros = 0
                    clan_cash = 0

                    if int(clan.guild) != f_interaction.guild.id:
                        clan_pros = int(clan.total_exp) / total_exp * 100
                        clan_cash = 15 * clan_pros / 100

                        clan.vault1 = str(int(clan.vault1) + int(clan_cash))
                        clan.total_income_from_mark_global = str(clan_cash) if not clan.total_income_from_mark_global else str(int(clan.total_income_from_mark_global) + int(clan_cash))
                        orm.commit()

                    components = [
                        [
                            Button(style=ButtonStyle.URL, url=link, label='Link'),
                            Button(style=ButtonStyle.blue, label='Local'),
                            Button(style=ButtonStyle.blue, label='Global')

                        ]
                    ]

                    if int(clan.guild) != f_interaction.guild.id:
                        components[0].insert(1, Button(style=ButtonStyle.URL, url=clan_link, label=' City'))

                    await self.bot.get_channel(int(clan.channel_marketplace_id)).send(
                        embed=emb,
                        components=components
                    )

                    if int(clan.guild) != f_interaction.guild.id:
                        clan_list.append(f'{clan._id}.{+ clan_cash}')
                        mess = await send_embed(
                            title='Vault1 top up (Marketplace)',
                            text=f'We earned {clan_cash} ECT',
                            color=BLUE_COLOR,
                            channel=self.bot.get_channel(int(clan.channel_logs_id))
                        )
                        msg_list.append(str(mess.id))

                        TransactionMain(
                            type='vault1_top_up_mark_global',
                            date=datetime.now(),
                            clan=str(clan._id),
                            msg_id=str(mess.id),
                            received_tokens=str(clan_cash),
                            vault1=clan.vault1,
                        )
                        orm.commit()

                except Exception as e:
                    await self._error(
                        'global send guild error: ', e, 
                        f_interaction.guild.id, f_interaction.guild.name
                    )
                    continue

            with contextlib.suppress(Exception):
                _components = [
                    [
                        Button(style=ButtonStyle.URL, url=link, label='Link'),
                        Button(style=ButtonStyle.blue, label='Global')

                    ]
                ]

                if f_interaction.guild.id != discord_config['server_main']:
                    _components[0].insert(1, Button(style=ButtonStyle.URL, url=clan_link,
                                                    label=' City'))

                await self.bot.get_channel(ether_city_channels['marketplace']).send(
                    embed=emb,
                    components=_components
                )

            await send_embed(
                text='Your NFT was published successfully across all the cities.\nEarned 25XP\n1 hour cooldown on publishing',
                color=GREEN_COLOR,
                member=f_interaction.user
            )

            MarkGlobal(
                user_id=str(f_interaction.user.id),
                from_clan=str(Clans.get(channel_marketplace_id=str(f_interaction.channel.id))._id) if f_interaction.guild.id != discord_config['server_main'] else 'main_server',
                link=link,
                date=str(datetime.now()),
                to_clans=clan_list,
                msg_list=msg_list
            )
            orm.commit()

            await self.bot.get_cog('rating').new_lvl(
                f_interaction.user.id
            )

            await self._log('send global marketplace: ', f_interaction.user.id, f_interaction.user.name)
            return True

    async def market_global_button(self: "Marketplace", f_interaction: Interaction) -> ty.Union[None, bool]:
        """
        Publishing an ad on the marketplace of all cities of the system
        """
        with orm.db_session:
            member: Members = Members.get(
                id=str(f_interaction.user.id),
            )

            if float(member.tokens) < 15:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='I couldn\'t reserve 15 ECT to publish your NFT globally.\n'
                                    ' Please top up the wallet in order to proceed.',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network'))
                return None

            dm = await f_interaction.author.create_dm()

            await f_interaction.respond(
                embed=discord.Embed(
                    description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                    color=discord.Colour.dark_blue()
                )
            )

            await self._log(
                'marketplace global used', f_interaction.user.id, 
                f_interaction.user.name, f_interaction.guild.id,
                f_interaction.guild.name
            )

            data, link = await self.check_link(f_interaction)

            if data is None or not data:
                return True

            elif len(data) > 0:
                msg, emb = await self.send_message_market(f_interaction, data)
                try:
                    msg_interaction = await self.bot.wait_for(
                        'button_click', timeout=120,
                        check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private and m.message == msg
                    )
                except asyncio.TimeoutError:
                    await timeout_error(f_interaction.user)
                    return None

                if msg_interaction.component.label == 'Cancel':
                    await invisible_respond(msg_interaction)
                    await send_embed(
                            text='You have canceled the sending of your NFT.',
                            color=RED_COLOR,
                            member=f_interaction.user
                    )
                    return False

                if msg_interaction.component.label == 'Publish':
                    await invisible_respond(msg_interaction)
                    clan_count = count(Clans.select())

                    _emb = discord.Embed(
                        description=f'I will post your NFT across {clan_count} cities for 15 ECT. Accept or decline.',
                        colour=GREEN_COLOR)

                    _msg = await f_interaction.user.send(
                        embed=_emb,
                        components=[
                            [
                                Button(style=ButtonStyle.green, label='Accept'),
                                Button(style=ButtonStyle.red, label='Decline')
                            ]
                        ]
                    )

                    try:
                        _msg_interaction = await self.bot.wait_for(
                            'button_click', timeout=120,
                            check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private and m.message == _msg
                        )
                    except asyncio.TimeoutError:
                        await timeout_error(f_interaction.user)
                        return None

                    if _msg_interaction.component.label == 'Accept':
                        await invisible_respond(_msg_interaction)
                        if float(Members.get(id=str(f_interaction.user.id)).tokens) >= 15:
                            return await self.__success_send(f_interaction, link, emb)

                        errors: int = 1
                        error_emb = discord.Embed(
                            description='That\'s strange. I was checking your balance before.\n'
                                        'But now you don\'t have enough ECT to publish globally.'
                                        'You can top up your wallet and retry afterwards.',
                            colour=RED_COLOR
                        ).set_footer(text=f'{errors}/5 attempts')
                        retry_msg = await f_interaction.user.send(
                            embed=error_emb,
                            components=[
                                [
                                    Button(style=ButtonStyle.blue, label='Retry')
                                ]
                            ]
                        )

                        while errors < 5:
                            try:
                                retry_msg_interaction = await self.bot.wait_for(
                                    'button_click', timeout=180,
                                    check=lambda
                                    m: m.channel.type == discord.ChannelType.private and m.message == retry_msg and m.user == f_interaction.user
                                )
                            except asyncio.TimeoutError:
                                await timeout_error(f_interaction.user)
                                return True
                            
                            if retry_msg_interaction.component.label == 'Retry':
                                await invisible_respond(retry_msg_interaction)
                                if float(Members.get(id=str(f_interaction.user.id)).tokens) >= 15:
                                    await retry_msg.delete()
                                    return await self.__success_send(f_interaction, link, emb)

                                errors += 1
                                if errors >= 5:
                                    await retry_msg.delete()
                                    break

                                await retry_msg.edit(
                                    embed=discord.Embed(
                                        description='Still nothing. Don\'t worry, I will be here. Waiting for you to retry',
                                        colour=RED_COLOR
                                    ).set_footer(text=f'{errors}/5 attempts'))
                                continue

                        await send_embed(
                            text='You exceeded the amount of attempts (5). Please, retry after the 10 min cooldown.',
                            color=RED_COLOR,
                            channel=f_interaction.user)
                        return True

                    elif _msg_interaction.component.label == 'Decline':
                        await invisible_respond(_msg_interaction)
                        await _msg.delete()
                        await send_embed(
                            text='Declined?! That\'s fine. You can publish your NFT any time later.',
                            color=RED_COLOR,
                            member=f_interaction.user)
                        return None


def setup(bot):
    bot.add_cog(Marketplace(bot))
    print(f'=== cogs {Marketplace.__name__} loaded ===')
