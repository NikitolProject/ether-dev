from sys import int_info
import time

import random
import asyncio
import datetime
import contextlib
import typing

import logging
import discord

from asyncio import events

from discord import User
from discord.ext import commands, tasks
from discord_components import Button, ButtonStyle

from . import BasicCog, discord_config, ether_city_channels
from .utils import *
from .database import *

reward_clans = {
    1: 150,
    2: 130,
    3: 110,
    4: 100,
    5: 90,
    6: 90,
    7: 85,
    8: 85,
    9: 80,
    10: 80
}


class ClansCog(BasicCog, name='clans'):

    b_reward_token: bool = False

    date = None
    clans: dict = {}
    used_users: set = set()

    message_banned: set = set()
    refresh_bans: dict = {}
    refresh_uses: dict = {}
    refresh_cool: set = set()

    def __init__(self: "ClansCog", bot: commands.Bot) -> None:
        super().__init__(bot)
        self._clan_statistics.start()
        self._update_clan_nods.start()
        self._random_token_reward.start()
    
    @classmethod
    async def update_top_members_in_clan(cls: "ClansCog", search: Clans = None) -> None:
        """
        Updating the list of clan members in the database, sorting by rating
        """
        await cls._log(
            cls, 'Updating the list of clan '
                 'members and sorting them by rating.'
        )
        if search is not None:
            await cls.__sorted_users_in_clan(cls, search)
            return None

        with orm.db_session:
            clans: Clans = Clans.select(lambda c: not c.frozen)
        
        for clan in clans:
            with contextlib.suppress(Exception):
                await cls.__sorted_users_in_clan(cls, clan)

    async def  __sorted_users_in_clan(self: "ClansCog", clan: Clans) -> None:
        members_rating: list = []
        members_rating_string_array: list = []
        members_to_sort: list = clan.nods
        members_to_sort.append(clan.owner_clan)
        members_to_sort = list(set(members_to_sort))

        with orm.db_session:
            for member in members_to_sort:
                member: Members = Members.get(id=member)
                members_rating.append({
                    'id': member.id,
                    'exp': int(member.exp_all) + int(member.exp_rank),
                    'rank': member.lvl_rank
                })

            members_rating: list = sorted(members_rating, key=lambda k: k['exp'], reverse=True)

            for key in members_rating:
                members_rating_string_array.append(
                    f'{key["id"]}:{key["exp"]}:{key["rank"]}'
                )
            
            clan.members_rating = list(set(members_rating_string_array))
            orm.commit()

    @classmethod
    async def clan_rating(cls: "ClansCog") -> None:
        """
        Calculation of rating positions of clans based on their experience
        """
        await cls._log(
            cls, 'Calculation of rating positions of clans based on their experience.'
        )
        
        with orm.db_session:
            clans: dict = {}
            for clan in Clans.select(lambda c: not c.frozen):
                members = clan.nods
                members.append(clan.owner_clan)
                clan_exp = await cls.__getting_exp_clan(cls, members)
                members.remove(clan.owner_clan)

                clans.update({clan.token: clan_exp})
                clan.total_exp = str(clan_exp)
                orm.commit()

            sorted_values = sorted(clans.values(), reverse=True)
            sorted_dict = {}
            for i in sorted_values:
                for k in clans.keys():
                    if clans[k] == i:
                        sorted_dict[k] = clans[k]

            await cls.__updating_exp_of_clan_members(cls, sorted_dict)

    async def __getting_exp_clan(self: "ClansCog", members: list) -> int:
        clan_exp: int = 0
        members = list(set(members))

        with orm.db_session:
            for m in members:
                member: Members = Members.get(id=str(m))
                if member is not None:
                    clan_exp += int(member.exp_all) + int(member.exp_rank)
                    await asyncio.sleep(0.1)
        return clan_exp

    async def __updating_exp_of_clan_members(self, sorted_dict: dict) -> None:
        with orm.db_session:
            for i in sorted_dict:
                if RatingClans.select().exists():
                    rating: RatingClans = RatingClans.get(token=i)
                    rating.clan_rate = str(int(list(sorted_dict).index(i)) + 1)
                    rating.total_exp = str(sorted_dict[i])

    @tasks.loop(seconds=30)
    async def _update_clan_nods(self: "ClansCog") -> None:
        await self._log(
            "Update count clan nods"
        )
        with orm.db_session:
            for clan in Clans.select(lambda c: not c.frozen):
                members_rating = list(set(clan.members_rating))
                nods = list(set(clan.nods))
                clan.nods = nods
                clan.members_rating = members_rating
                orm.commit()

    @tasks.loop(minutes=1)
    async def _clan_statistics(self: "ClansCog") -> None:
        """
        Update clan statistics and daily rewards
        """
        await self._log(
            'Update clan statistics and daily rewards.'
        )
        with orm.db_session:
            clans: list = Clans.select(lambda c: not c.frozen)
            for clan in clans:
                try:
                    members, supports, count = await self.__member_clan_list(clan)
                    invite_link = await check_invites_guild(
                        self.bot.get_guild(int(clan.guild)), clan
                    )
                    if RatingClans.get(clan_id=str(clan._id)) is None:
                        RatingClans(
                            clan_id=clan._id,
                            token=clan.token,
                            name=clan.name,
                            invite_link=str(invite_link),
                            channel_statistics_id=clan.channel_statistics_id,
                            msg_statistics_id=clan.msg_statistics_id,
                            guild=clan.guild,
                            members=str(members),
                            supports=str(supports),
                            member_count=str(count + 1),
                            total_exp='Installed',
                            clan_rate='Installed',
                            last_list=[]
                        )
                        orm.commit()
                        continue

                    rating: RatingClans = RatingClans.get(clan_id=str(clan._id))
                    rating.members = list(set(members))
                    rating.supports = list(set(supports))
                    rating.members_count = str(count)
                    orm.commit()

                except Exception as e:
                    await self._error(
                        'Error updating clan statistics: ' + str(e)
                    )
                   #  RatingClans.get(clan_id=str(clan._id)).delete()

            await asyncio.gather(
                self.clan_rating(), self.update_top_members_in_clan(), 
                self.bot.get_cog('statistics').statistics()
            )

    async def __member_clan_list(
        self: "ClansCog", clan: typing.Union[None, Clans] = None, 
        _id: typing.Union[int, bool] = False
    ) -> tuple:
        """
        Counting the number of clan members/assistants
        """
        members: list = []
        supports: list = []
        count = 0

        await self._log(
            f'Counting the number of clan members/assistants {clan.name}.'
        )
        with orm.db_session:
            for member in clan.nods:
                with contextlib.suppress(Exception):
                    member: discord.User = self.bot.get_user(int(member))
                    members.append(member.mention) if not _id else members.append(int(member.id))
                    count += 1

            for support in clan.supports:
                with contextlib.suppress(Exception):
                    support: discord.User = self.bot.get_user(int(support))
                    if support.mention not in members:
                        count += 1
                    supports.append(support.mention) if not _id else members.append(int(support.id))

        return list(set(members)), list(set(supports)), count


    async def stats_clan(self: "ClansCog", f_interaction: Interaction) -> None:
        """
        Updating a message with clan statistics
        """
        await self._log(
            f'Updating a message with clan statistics {f_interaction.user.name}.'
        )

        with orm.db_session:
            rating: RatingClans = RatingClans.get(
                msg_statistics_id=str(f_interaction.message.id)
            )
            if rating is None:
                return None
            
            clan: Clans = Clans.get(_id=rating.clan_id)

            if self.refresh_bans.get(clan.token) is not None and f_interaction.user.id in self.refresh_bans[clan.token]:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='Being active is good. You can successfully refresh only one time per 5 hours.',
                        colour=RED_COLOR
                    )
                )
                return None
            
            if self.refresh_uses.get(clan.token) is not None and f_interaction.user.id in \
                self.refresh_uses[clan.token][0].keys() and self.refresh_uses.get(clan.token)[0][f_interaction.user.id] > 5:
                await f_interaction.respond(embed=discord.Embed(
                    description='15 min. cooldown is still applied to you',
                    colour=RED_COLOR
                ))
                return None

            if f_interaction.message.id in self.message_banned:
                await f_interaction.respond(embed=discord.Embed(
                    description='15 min. cooldown is still in progress since the last refresh',
                    colour=RED_COLOR
                ))
                return None
            
            rating: RatingClans = RatingClans.get(
                msg_statistics_id=str(f_interaction.message.id)
            )
            vault0_tokens: float = sum(float(t.split(":")[1]) for t in clan.vault0)
            new_list: list = [
                rating.clan_rate, rating.total_exp,
                rating.members_count, str(vault0_tokens),
                clan.vault1
            ]

            if new_list != rating.last_list:
                await self.__success_refresh(f_interaction, rating, clan, vault0_tokens, new_list)
                return None

            clan_refresh_uses = self.refresh_uses.get(clan.token)
            if clan_refresh_uses is None:
                self.refresh_uses.update({clan.token: [{f_interaction.user.id: 2}]})

            elif f_interaction.user.id not in self.refresh_uses[clan.token][0].keys():
                self.refresh_uses[clan.token][0].update({f_interaction.user.id: 2})

            elif clan_refresh_uses[0][f_interaction.user.id] >= 5:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='You\'ve exceeded the amount of attempts (5). 15 min. cooldown is applied.',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network'))
                await asyncio.sleep(900)
                self.refresh_uses[clan.token][0].pop(f_interaction.user.id)
                return None
            
            else:
                self.refresh_uses[clan.token][0].update(
                    {f_interaction.user.id: clan_refresh_uses[0][f_interaction.user.id] + 1}
                )

            await f_interaction.respond(
                embed=discord.Embed(
                description='The city is steady...is steady in not evolving. Nothing to see here. Nothing to '
                            'refresh. Come back when something happens.',
                colour=RED_COLOR
                )
            )
            orm.commit()

    async def __success_refresh(
        self: "ClansCog", f_interaction: Interaction, 
        rating: RatingClans, clan: Clans,
        vault0_tokens: float, new_list: list
    ) -> None:
        await send_interaction_respond(
            f_interaction, discord.Embed(
                description='You\'ve won 1 ECT\nAnd now we '
                            'all know the new stats of our city! Thank you!',
                colour=GREEN_COLOR
            )
        )

        emb = discord.Embed(
            title=f'City Stats',
            colour=INVISIBLE_COLOR,
            description=f"**Rating**: {rating.clan_rate}\n"
                        f"**City XP**: {rating.total_exp}\n"
                        f"**DC**: {rating.members_count}\n"
                        f"**Vault0**: {vault0_tokens} ECT\n"
                        f"**Vault1**: {clan.vault1} ECT\n"
                        f"**Vaults**: {vault0_tokens + float(clan.vault1)} ECT\n"
                        f"**Battles count**: *soon*\n"
                        f"**Earned from battles**: *soon*\n\n\n\n"
                        f"You can update stats by clicking on the 'Refresh' button below.\n"
                        f"The first one to update with new details will win 1 ECT. But be careful with multi clicking.\n"
                        f"You have 5 attempts before a cooldown."
        )
        rating.last_list = new_list
        member: Members = Members.get(id=str(f_interaction.user.id))
        member.tokens = str(float(member.tokens) + 1)
        TransactionMain(
            type="refresh_reward",
            date=datetime.now(),
            clan=str(clan._id),
            client=str(f_interaction.user.id),
            sum="1"
        )
        orm.commit()

        with contextlib.suppress(Exception):
            await f_interaction.respond(embed=emb)
            channel = f_interaction.guild.get_channel(int(clan.channel_logs_id))
            await send_embed(
                text=f'{f_interaction.user.mention} just updated our stats and won 1 ECT\n',
                color=BLUE_COLOR,
                channel=channel
            )

        await self._log(
            'success refresh stats: ', f_interaction.user.id, 
            f_interaction.user.name, 'clan:', clan.token
        )
        self.message_banned.add(f_interaction.message.id)
        if self.refresh_bans.get(clan.token) is None:
            self.refresh_bans.update({clan.token: []})

        if self.refresh_uses.get(clan.token) is not None:
            self.refresh_uses.pop(clan.token)

        self.refresh_bans[clan.token].append(f_interaction.user.id)
        await asyncio.sleep(900)
        self.message_banned.remove(f_interaction.message.id)
        await asyncio.sleep(17100)
        self.refresh_bans[clan.token].remove(f_interaction.user.id)

    @tasks.loop(hours=random.randint(1, 24))
    async def _random_token_reward(self: "ClansCog") -> None:
        """
        An event giving 1 ECT to a random clan member
        """
        await self._log(
            'An event has started giving 1 ECT to a random clan member'
        )
        if self.date == datetime.datetime.now().date():
            await self.__tokens_reward()
            return None

        with orm.db_session:
            self.date = datetime.datetime.now().date()
            self.clans.clear()
            self.used_users.clear()
            clans: Clans = Clans.select(lambda c: not c.frozen)

            for clan in clans:
                if len(clan.nods) >= 20:
                    size = len(clan.nods) / 100 * 5
                    print(size)
                    self.clans.update({clan.token: [0, int(size)]})
            await self.__tokens_reward()
            orm.commit()

    async def __tokens_reward(self: "ClansCog") -> None:
        with orm.db_session:
            for key, value in self.clans.items():
                with contextlib.suppress(Exception):
                    if value[0] < value[1]:
                        _clan = Clans.get(token=key)
                        nods = list(_clan.nods)
                        nods.append(_clan.owner_clan)

                        await self.__user_selection(
                            nods, _clan, key, value
                        )
                        nods.remove(_clan.owner_clan)

    async def __user_selection(
        self: "ClansCog", nods: list, _clan: Clans, 
        key: str, value: ty.Any
    ) -> None:
        while any(nods):
            with orm.db_session:
                user: str = random.choice(nods)

                if user in self.used_users:
                    nods.remove(user)
                    continue

                self.clans[key][value[0]] += 1
                self.used_users.add(user)
                member: Members = Members.get(id=user)
                member.tokens = str(int(member.tokens) + 1)
                await send_embed(
                    text=f'Random winner for 1 ECT - {self.bot.get_user(int(user)).mention}',
                    color=BLUE_COLOR,
                    channel=self.bot.get_channel(_clan.channel_logs_id)
                )
                await send_embed(
                    title='Random ECT for a random DC',
                    text=f'+1 ECT for you!',
                    color=BLUE_COLOR,
                    member=self.bot.get_user(int(user))
                )

                TransactionMain(
                    type="random_get_one_token",
                    date=datetime.datetime.now(),
                    clan=_clan._id,
                    user_id=user
                )
                orm.commit()
                break

    @_update_clan_nods.before_loop
    async def before_update_clan_nods(self: "ClansCog") -> None:
        """
        Initialization of the update_clan_nods event
        """
        await self._log(
            'Initialization of the update_clan_nods event'
        )

        await self.bot.wait_until_ready()

    @_clan_statistics.before_loop
    async def _before_clan_statistics(self) -> None:
        """
        Initialization of the clan_statistics event
        """
        await self._log(
            'Initialization of the clan_statistics event begins'
        )
        await self.bot.wait_until_ready()

    @_random_token_reward.before_loop
    async def _before_random_token_reward(self: "ClansCog") -> None:
        """
        Initializing the random_token_reward event
        """
        await self._log(
            'Initialization of the random_token_reward event begins'
        )
        await asyncio.sleep(random.randint(1, 24) * 60 * 60)
        await self.bot.wait_until_ready()

    async def reward_top_clans(self: "ClansCog") -> None:
        """
        Distribution of the 10 best clans awards for rating
        """
        await self._log(
            'The event of distribution of the 10 best clans of the rating awards begins'
        )

        with orm.db_session:
            rating: list = RatingClans.select().order_by(
              lambda r: desc(int(r.clan_rate))
            )[:10]

            for rate in rating:
                clan: Clans = Clans.get(
                    _id=int(rate.clan_id)
                )
                clan.vault1 = str(int(clan.vault1) + reward_clans[int(rate.clan_rate)])

                TransactionMain(
                    type="vault1_reward",
                    date=datetime.now(),
                    clan=str(clan._id),
                    received_tokens=str(reward_clans[int(rate.clan_rate)]),
                    rate=rate.clan_rate,
                    vault1=clan.vault1
                )

                await send_embed(
                    title='Vault1 top up (TOP 10)',
                    text=f'Our place is #{rate.clan_rate}\nWe earned {reward_clans[int(rate.clan_rate)]} ECT',
                    color=BLUE_COLOR,
                    channel=self.bot.get_channel(int(clan.channel_logs_id))
                )

                await asyncio.sleep(1)

            orm.commit()

        await self.__tokens_vault1()

    async def __tokens_vault1(self: "ClansCog") -> None:
        """
        Drop storage of 1 clans
        """
        await self._log(
            'The drop of the storage of 1 clans begins'
        )

        with orm.db_session:
            for clan in Clans.select(lambda c: not c.frozen):
                if int(clan.vault1) < 0:
                    continue

                total_tokens: float = sum(
                    [float(token.split(":")[1]) for token in clan.vault0]
                )

                vault1 = int(clan.vault1)
                clan.vault0 = list(set(clan.vault0))
                orm.commit()

                for i in range(len(clan.vault0)):
                    try:
                        rate: float = float_round(
                            100 / total_tokens * float(clan.vault0[i].split(":")[1]), 4
                        )
                        received_tokens: int = round(vault1 / 100 * rate, 9)
                        await self.__drop_tokens_in_database(
                            i, clan, rate, clan.vault0[i], received_tokens, vault1
                        )

                        await send_embed(
                            title=f'Daily Drop! Drop! Drop!',
                            text=f'+ **{received_tokens}** ECT dropped on your balance from {clan.token}. {clan.name} Vault1\n',
                            color=BLUE_COLOR,
                            member=self.bot.get_user(int(clan.vault0[i].split(":")[0])))

                    except Exception as e:
                        await self._error(
                            f"An error has occurred: {e}"
                        )

                clan.vault1 = str(int(clan.vault1) - vault1)
                await asyncio.sleep(1)
            orm.commit()

    async def __drop_tokens_in_database(
        self, i, clan: Clans, rate: int, user: list, 
        received_tokens: int, vault1: typing.Any
    ) -> None:
        with orm.db_session:
            clan.vault0[i].split(":")[1] = str(
                float(user.split(":")[1]) + received_tokens
            )
            clan.vault0[i].split(":")[2] = str(rate)
            Members.get(id=user.split(":")[0]).tokens = str(
                float(Members.get(id=user.split(":")[0]).tokens) + received_tokens
            )
            TransactionMain(
                type="vault1_drop",
                date=datetime.now(),
                clan=str(clan._id),
                to_user=user.split(":")[0],
                received_tokens=str(received_tokens),
                rate=str(rate),
                vault1=str(vault1)
            )
            orm.commit()

    @classmethod
    async def top_clans(cls: "ClansCog", f_interaction: Interaction) -> None:
        """
        Conclusion of the top 10 clans
        """
        await cls._log(
            cls, f'{f_interaction.user.name} looks at the top 10 clans'
        )

        with orm.db_session:
            rating: list = RatingClans.select().order_by(
              lambda r: desc(int(r.clan_rate))
            )[:10]
            rating.reverse()
            embed = discord.Embed(title='Top-10 cites', colour=INVISIBLE_COLOR)
            for clan in rating:
                embed.add_field(
                    name=f'**#{clan.clan_rate}│** `{clan.name}` ',
                    value=f'Members: **{clan.members_count}**\n'
                        f'Total xp: **{clan.total_exp}**\n'
                        f'Link: {clan.invite_link}',
                    inline=False
                )

        await f_interaction.respond(embed=embed)

    async def top_members(self: "ClansCog", f_interaction: Interaction) -> None:
        """
        Output of the top 10 users
        """
        await self._log(
            f'{f_interaction.user.name} looks at the top 10 users'
        )

        with orm.db_session:
            rating: Members = Members.select().order_by(
                lambda m: desc(int(m.exp_all) + int(m.exp_rank))
            )[:10]
            
            embed = discord.Embed(title='Top-10 DeCitizens', colour=INVISIBLE_COLOR)
            for i, u in enumerate(rating, start=1):
                with contextlib.suppress(Exception):
                    embed.add_field(
                        name=f'**{i}:** `{self.bot.get_user(int(u.id)).name}`',
                        value=f'Lvl: **{u.lvl_rank}**\n'
                            f'XP: **{int(u.exp_all) + int(u.exp_rank)}**\n',
                        inline=False
                    )

        await f_interaction.respond(embed=embed)

    async def member_cities(self: "ClansCog", f_interaction: Interaction) -> None:
        """
        The output of the cities in which the user consists
        """
        await self._log(
            f'{f_interaction.user.name} looks at the cities in which it consists'
        )
        with orm.db_session:
            user: Members = Members.get(id=str(f_interaction.user.id))
            cities: list = user.clans_id

            if not cities:
                embed = discord.Embed(
                    description=f'You haven\'t joined any cities yet. Check the list in '
                                f'the {self.bot.get_channel(ether_city_channels["cities"]).mention} channel', 
                    colour=RED_COLOR)
                await f_interaction.respond(embed=embed)
                return None

            embed = discord.Embed(title='My cities', colour=INVISIBLE_COLOR)
            count: int = 0
            for c_id in cities:
                clan: Clans = Clans.get(_id=int(c_id))
                if clan is None:
                    continue

                count += 1
                embed.add_field(
                    name=f'{count}. {clan.name}',
                    value=f'Link: {clan.invite_link}',
                    inline=False
                )

                if count == 10:
                    break

        await f_interaction.respond(embed=embed)

    async def members_clan(self: "ClansCog", f_interaction: Interaction) -> None:
        """
        Withdrawal of clan members
        """
        await self._log(
            f'{f_interaction.user.name} looks at the number of clan members'
        )

        with orm.db_session:
            clan: Clans = Clans.get(channel_statistics_id=str(f_interaction.channel.id))

            emb = discord.Embed(title=f'{clan.token}. {clan.name}', color=INVISIBLE_COLOR)

            for i, member in enumerate(list(reversed(clan.members_rating)), start=1):
                emb.add_field(
                    name=f'**{i}**: `{self.bot.get_user(int(member.split(":")[0]))}`', 
                    value=f'Lvl: {member.split(":")[1]}\nXP: {member.split(":")[2]}', 
                    inline=False
                )

                if i == 10:
                    break

        await f_interaction.respond(embed=emb)

    async def join_to_clan(self: "ClansCog", f_interaction: Interaction) -> None:
        """
        Joining a member to the clan (1)
        """
        await self._log(
            f'{f_interaction.user.name} joins the clan'
        )

        with orm.db_session:
            clan: Clans = Clans.get(channel_join_id=str(f_interaction.channel.id))
            member: Members = Members.get(id=str(f_interaction.user.id))

            if member.clans_id and str(clan._id) in member.clans_id:
                embed = discord.Embed(
                    description=f'You have already joined the clan {clan.name}', 
                    colour=RED_COLOR
                )
                await f_interaction.respond(embed=embed)
                return None

            if float(Members.get(id=str(f_interaction.user.id)).tokens) < 5.0:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='I couldn\'t reserve 5 ECT for you to join the city. Please top up the wallet in order to proceed.',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network'))
                return True
            
            if f_interaction.guild.get_role(int(clan.role_nods_id)).position > f_interaction.guild.self_role.position:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='Ethers of the city moved my rights too low on the server.\n'
                                    'I cannot help you with joining.'
                                    f' But I notified {f_interaction.guild.get_member(int(clan.owner_clan)).mention} to do something about it.',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network'))

                await send_embed(
                    text=f'People tried to join {clan.name}. But failed.\nBecause my rights on the server are lower than Nods.',
                    color=RED_COLOR,
                    member=f_interaction.guild.get_member(int(clan.owner_clan))
                )
                return True

            msg = await send_embed(
                text='Great, I just need your confirmation to deposit 5 ECT into the city\'s vault.\n'
                        'It will make you a co-owner of the city.\n'
                        'So the daily profit collected by the city will be distributed to you based on your share percentage.',
                color=GREEN_COLOR,
                member=f_interaction.user,
                interaction=f_interaction
            )
            dm = await f_interaction.author.create_dm()

            await f_interaction.respond(
                embed=discord.Embed(
                    description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                    color=discord.Colour.dark_blue()
                )
            )
            await msg.edit(
                components=[
                    [
                        Button(style=ButtonStyle.green, label=' Join'),
                        Button(style=ButtonStyle.red, label='Decline')
                    ]
                ]
            )

            try:
                msg_interaction = await self.bot.wait_for(
                    'button_click', timeout=60,
                    check=lambda m: m.channel.type == discord.ChannelType.private and m.message == msg and m.user == f_interaction.user
                )
            except asyncio.TimeoutError:
                await msg.delete()
                return True

            if msg_interaction.component.label == 'Decline':
                await send_embed(
                    text='Declined?! That\'s fine. You can join at any time.',
                    color=RED_COLOR,
                    member=f_interaction.user,
                    interaction=msg_interaction)
                await invisible_respond(msg_interaction)
                return True

            if msg_interaction.component.label == ' Join':
                await invisible_respond(msg_interaction)
                if float(Members.get(id=str(f_interaction.user.id)).tokens) >= 5:
                    await self.join_to_clan_accept(f_interaction, clan)
                    return True

                errors: int = 1
                emb = discord.Embed(
                    description='That\'s strange. I was checking your balance before.\n'
                                'But now you don\'t have enough ECT to join the city. You can top up your wallet and retry afterwards.',
                    colour=RED_COLOR
                ).set_footer(text=f'{errors}/5 attempts')
                _msg = await f_interaction.user.send(
                    embed=emb,
                    components=[
                        [
                            Button(style=ButtonStyle.blue, label='Retry')
                        ]
                    ]
                )
                while errors < 5:
                    try:
                        _msg_interaction = await self.bot.wait_for(
                            'button_click', timeout=180,
                            check=lambda m: m.channel.type == discord.ChannelType.private and m.message == _msg and m.user == f_interaction.user
                        )
                    except asyncio.TimeoutError:
                        await msg.delete()
                        return True

                    if _msg_interaction.component.label == 'Retry':
                        await invisible_respond(_msg_interaction)

                        if float(Members.get(id=str(f_interaction.user.id)).tokens) < 5:
                            errors += 1
                            if errors >= 5:
                                await _msg.delete()
                                break

                            await _msg.edit(
                                embed=discord.Embed(
                                    description='Still nothing. Don\'t worry, I will be here. Waiting for you to retry',
                                    colour=RED_COLOR
                                ).set_footer(text=f'{errors}/5 attempts'))

                        if float(Members.get(id=str(f_interaction.user.id)).tokens) >= 5:
                            await _msg.delete()
                            await self.join_to_clan_accept(f_interaction, clan)
                            return True

                await send_embed(
                    text='You exceeded the amount of attempts (5). Please, retry after the 10 min cooldown.',
                    color=RED_COLOR,
                    channel=f_interaction.user,
                    interaction=f_interaction
                )

    async def join_to_clan_accept(self: "ClansCog", f_interaction: Interaction, clan: Clans) -> None:
        """
        Joining a member to the clan (2)
        """
        await self._log(
            f'{f_interaction.user.name} joins the clan'
        )

        with orm.db_session:
            member: Member = f_interaction.guild.get_member(
                f_interaction.user.id
            )

            role = f_interaction.guild.get_role(
                int(clan.role_nods_id)
            )
            owner_clan: Member = self.bot.get_user(int(clan.owner_clan))

            clan.nods.append(str(member.id))
            clan.vault0.append(f"{f_interaction.user.id}:{5}:{0}")

            mem: Members = Members.get(id=str(f_interaction.user.id))
            mem.clans_id.append(str(clan._id))
            mem.tokens = str(float(mem.tokens) - 5)

            orm.commit()

            mem: Members = Members.get(id=str(f_interaction.user.id))

            if not mem.nods_status:
                mem.nods_status = True

            await self._log(
                f"members join to clan: {f_interaction.user.id} {f_interaction.user.name}, "
                f"clan:, {clan.token}"
            )

            if str(member.id) not in clan.history_nods:
                clan.history_nods.append(str(member.id))
                mem.exp_rank = str(int(mem.exp_rank) + 100)

            orm.commit()

            for guild in member.mutual_guilds:
                guild_member = guild.get_member(member.id)
                await self.bot.get_cog('rating').check_status(guild_member)

            await vault0_refresh(clan)

            await send_embed(
                title='+1 Nods in the city',
                text=f'Welcome {member.mention}!',
                color=BLUE_COLOR,
                channel=f_interaction.guild.get_channel(int(clan.channel_logs_id)))

            await send_embed(
                text=f'Look what you\'ve done:\n'
                    f'1. Made {clan.name} more powerful\n'
                    f'2. Staked 5 ECT into the city\'s vault\n'
                    f'3. Got a new role - Nods\n'
                    f'4. Received 100 XP',
                color=GREEN_COLOR,
                member=member
            )

            await send_embed(
                title=f'You\'ve got new Nods in {f_interaction.channel.category.name}',
                text=f'Meet the: {member.mention}',
                color=GREEN_COLOR,
                member=owner_clan
            )

            await self.bot.get_cog('rating').new_lvl(
                mem.id, 
                send_msg=False
            )
            await self.bot.get_cog('rating').new_lvl(
                mem.id
            )
            await member.add_roles(role)
            orm.commit()

        return True

    async def member_profile(self: "ClansCog", f_interaction: Interaction) -> None:
        """
        Displays the user profile
        """
        await self._log(
            f'{f_interaction.user.name} viewing the profile'
        )
        with orm.db_session:
            try:
                user: Members = Members.get(id=str(f_interaction.user.id))
                to_exp = await self.bot.get_cog('rating').check_rank_lvl(f_interaction.user.id, user_info=True)

                clan: Clans = Clans.get(channel_wallet_id=str(f_interaction.channel.id)) if Clans.select().exists() else None
                
                description = f'ECT: {user.tokens}\n'
                description += f'Level: {user.lvl_rank}\n'
                description += f'XP: {int(user.exp_all) + int(user.exp_rank)}\n'
                description += f'XP to level {int(user.lvl_rank) + 1}: {to_exp - int(user.exp_rank)}\n'
                
                if clan is not None:             
                    for u in clan.vault0:
                        if int(u.split(":")[0]) == f_interaction.user.id:
                            description += f"Vault0: {u.split(':')[1]}"
                            description += f" ECT ({u.split(':')[2]}%)\n"
                            description += f"Vault1: {round(float(clan.vault1) / 100 * float(u.split(':')[2]), 9)} ECT ({clan.vault1} ECT)"
                            break

                emb = discord.Embed(
                    title='Profile',
                    description=description,
                    colour=INVISIBLE_COLOR
                )
                await f_interaction.respond(embed=emb)
            
            except Exception as e:
                await self._error(
                    e, f_interaction.user, f_interaction.channel
                )
    
    async def tokens_transfer(self: "ClansCog", f_interaction: Interaction) -> ty.Union[bool, None]:
        """
        Transfer of tokens between users
        """
        await self._log(
            f'{f_interaction.user.name} transfers tokens'   
        )

        with orm.db_session:
            if float(Members.get(id=str(f_interaction.user.id)).tokens) <= 0.0:

                await f_interaction.respond(
                    embed=discord.Embed(
                        description='Your balance is 0 ECT. I cannot send 0 ECT to anyone. Even to myself.',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network')
                )
                return None

            dm = await f_interaction.author.create_dm()

            await f_interaction.respond(
                embed=discord.Embed(
                    description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                    color=discord.Colour.dark_blue()
                )
            )

            await send_embed(
                text='Reply with recipient\'s id. To get user\'s id use this guide\n'
                        'https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-',
                color=INVISIBLE_COLOR,
                interaction=f_interaction,
                member=f_interaction.user
            )
            await invisible_respond(f_interaction)

            errors: int = 0
            error_msg: str = None
            while errors < 5:
                try:
                    _id = await self.bot.wait_for(
                        'message', timeout=120,
                        check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private
                    )
                except asyncio.TimeoutError:
                    await timeout_error(f_interaction.user)
                    return None

                try:
                    member = self.bot.get_user(int(_id.content))
                    if Members.get(id=str(member.id)) is None:
                        raise TypeError

                    elif member.id == f_interaction.user.id:
                        errors += 1
                        if errors < 5:
                            error_msg = await self.__msg_error(
                                errors, f_interaction
                            )
                        continue

                except Exception:
                    errors += 1
                    if errors < 5:
                        error_msg = await self.__msg_error(
                            errors, f_interaction
                        )
                    continue

                await send_embed(
                    text=f'Your current balance is **{Members.get(id=str(f_interaction.user.id)).tokens}** ECT\n'
                            f'How many ECT would you like to send?',
                    color=INVISIBLE_COLOR,
                    member=f_interaction.user
                )
                return await self.__transfer_currency(
                    f_interaction, errors, member
                )

            await error_msg.edit(
                embed=discord.Embed(
                    description='You exceeded the amount of attempts (5). Please, retry after the 10 min cooldown.',
                    colour=RED_COLOR
                )
            )
        return True

    async def __transfer_currency(
        self: "ClansCog", f_interaction: Interaction, errors: int, member: User
    ) -> bool:
        while errors < 5:
            try:
                cash = await self.bot.wait_for(
                    'message', timeout=120,
                    check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private
                )
            except asyncio.TimeoutError:
                await timeout_error(f_interaction.user)
                return False

            try:
                cash = float(cash.content)
                cash = float_round(cash, 9)

            except ValueError:
                errors += 1
                if errors < 5:
                    error_msg = await send_embed(
                        title='Ok! There is something wrong.',
                        text='Please, retry',
                        color=RED_COLOR,
                        member=f_interaction.user,
                        footer=f'{errors}/5 attempts'
                    )
                continue
            
            with orm.db_session:
                tokens: float = float(Members.get(id=str(f_interaction.user.id)).tokens)

            if tokens < cash or tokens <= 0:
                errors += 1
                if errors < 5:
                    error_msg = await self.__tokens_not_found(
                        errors, tokens, f_interaction
                    )
                continue

            emb = discord.Embed(
                description=f'Just to be sure. You want to send **{cash}** ECT to {member.mention}?',
                colour=GREEN_COLOR
            )
            msg = await f_interaction.user.send(
                embed=emb,
                components=[
                    [
                        Button(style=ButtonStyle.green, label=' Send'),
                        Button(style=ButtonStyle.red, label='Decline')
                    ]
                ]
            )

            try:
                msg_interaction = await self.bot.wait_for(
                    'button_click', timeout=120,
                    check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private and m.message == msg
                )
            except asyncio.TimeoutError:
                await timeout_error(f_interaction.user)
                return False

            if msg_interaction.component.label == 'Decline':
                await invisible_respond(msg_interaction)
                await send_embed(
                    text='Declined?! That\'s fine. You can send ECT at any time.',
                    color=RED_COLOR,
                    member=f_interaction.user)
                return False

            elif msg_interaction.component.label == ' Send':
                await invisible_respond(msg_interaction)
                with orm.db_session:
                    tokens: float = float(Members.get(id=str(f_interaction.user.id)).tokens)

                if tokens < cash or tokens <= 0:
                    errors += 1
                    if errors < 5:
                        await self.__tokens_not_found(
                            errors, tokens, f_interaction
                        )
                    continue
                
                with orm.db_session:
                    mem: Members = Members.get(id=str(member.id))
                    mem.tokens = str(float(mem.tokens) + cash)
                    Members.get(id=str(f_interaction.user.id)).tokens = str(
                        float(Members.get(id=str(f_interaction.user.id)).tokens) - cash
                    )

                    await send_embed(
                        title='Perfect!',
                        text=f'Your **{cash}** ECT has been sent to {member.mention}\n'
                                f'Balance: {Members.get(id=str(f_interaction.user.id)).tokens} ECT',
                        color=GREEN_COLOR,
                        member=f_interaction.user
                    )

                    await send_embed(
                        title='Nice! Money has arrived.',
                        text=f'{f_interaction.user.mention} sent you **{cash}** ECT',
                        color=GREEN_COLOR,
                        member=member
                    )

                    await send_log_channel(
                        title='Send tokens',
                        text=f'**{cash}** ECT transfer from {f_interaction.user.mention} to {member.mention}',
                        bot=self.bot
                    )

                    print(f'tokens transfer from {str(f_interaction.user.name)}, to {str(member.name)} - `{cash}`')

                    TransactionMain(
                        from_user=str(f_interaction.user.id),
                        to_user=str(member.id),
                        sum=str(cash),
                        date=datetime.now()
                    )
                    await asyncio.sleep(3)
                return False

    async def __tokens_not_found(
        self: "ClansCog", _errors: int, tokens: int, f_interaction: Interaction
    ) -> typing.Union[discord.Message, None]:
        _msg = await send_embed(
            title='Insufficient funds',
            text=f'Balance: **{tokens}**\n'
                    f'Please, reply with correct ECT amount that you want to send',
            color=RED_COLOR,
            member=f_interaction.user,
            footer=f'{_errors}/5 attempts')
        return _msg

    async def __msg_error(
        self: "ClansCog", errors: int, f_interaction: Interaction
    ) -> typing.Union[discord.Message, None]:
        return await send_embed(
            text='Wrong id. Please retry',
            footer=f'{errors}/5 attempts',
            color=RED_COLOR,
            member=f_interaction.user
        )

    async def top_up(self: "ClansCog", f_interaction: Interaction) -> None:
        """
        Replenishment of the 0 storage in the clan from the user
        """
        await self._log(
            f"{f_interaction.user.name} replenishes the clan's storage at number 0"
        )
        
        with orm.db_session:
            if float(Members.get(id=str(f_interaction.user.id)).tokens) <= 0:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='Your balance is 0 ECT. I cannot top up city\'s Vault0 with 0 ECT. People will riot.',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network')
                )
                return None

            clan: Clans = Clans.get(channel_wallet_id=str(f_interaction.channel.id))
            user: list = [i for i in clan.vault0 if i.split(":")[0] == str(f_interaction.user.id)]

            await send_embed(
                title='Top up',
                text=f'Balance: **{Members.get(id=str(f_interaction.user.id)).tokens}** ECT\n'
                    f'Vault0 share: {user[0].split(":")[1]} ECT ({user[0].split(":")[2]}%)\n'
                    f'Reply with the amount of ECT you want to top up the Vault0 with',
                color=INVISIBLE_COLOR,
                interaction=f_interaction,
                member=f_interaction.user
            )
            dm = await f_interaction.author.create_dm()

            await f_interaction.respond(
                embed=discord.Embed(
                    description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                    color=discord.Colour.dark_blue()
                )
            )

            errors = 0
            error_msg = None
            while errors < 5:
                try:
                    cash = await self.bot.wait_for(
                        'message', timeout=120,
                        check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private
                        or m.author.id == 905453765275029514 and m.channel.type == discord.ChannelType.private
                    )
                except asyncio.TimeoutError:
                    await timeout_error(f_interaction.user)
                    return None

                try:
                    if cash.author.id == 905453765275029514:
                        print("OOOOOOOOOOOOOOOOOOOOOK!")
                        return None

                    cash = float(cash.content)
                    cash = float_round(cash, 9)
                except ValueError:
                    errors += 1
                    if errors < 5:
                        await send_embed(
                            title='Ok! There is something wrong.',
                            text='Please, retry',
                            color=RED_COLOR,
                            member=f_interaction.user,
                            footer=f'{errors}/5 attempts'
                        )
                    continue

                tokens: float = float(Members.get(id=str(f_interaction.user.id)).tokens)

                if tokens < cash or tokens <= 0:
                    errors += 1
                    if errors < 5:
                        await send_embed(
                            text='That\'s strange. I was checking your balance before.\n'
                                f' But now it\'s less ({tokens}) than the requested amount.\n'
                                ' Please reply with new ECT amount or deposit ECT into your wallet.',
                            color=RED_COLOR,
                            member=f_interaction.user,
                            footer=f'{errors}/5 attempts'
                        )
                    continue

                emb = discord.Embed(
                    description=f'Just to be sure. You want to top up Vault0 of {clan.name} with **{cash}** ECT',
                    colour=GREEN_COLOR
                )
                msg = await f_interaction.user.send(
                    embed=emb,
                    components=[
                        [
                            Button(style=ButtonStyle.green, label=' Top up'),
                            Button(style=ButtonStyle.red, label='Decline')
                        ]
                    ]
                )

                try:
                    msg_interaction = await self.bot.wait_for(
                        'button_click', timeout=120,
                        check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private and m.message == msg
                    )
                except asyncio.TimeoutError:
                    await timeout_error(f_interaction.user)
                    return None

                if await self.__replenishment_clan_storage(msg_interaction, f_interaction, cash, errors, clan):
                    return None

    async def __replenishment_clan_storage(
        self: "ClansCog", msg_interaction: Interaction, f_interaction: Interaction, 
        cash: int, errors: int, clan: Clans
    ) -> bool:
        with orm.db_session:
            if msg_interaction.component.label == 'Decline':
                await invisible_respond(msg_interaction)
                await send_embed(
                    text='Declined?! That\'s fine. You can top up the Vault0 at any time.',
                    color=RED_COLOR,
                    member=f_interaction.user
                )
                return True

            elif msg_interaction.component.label == ' Top up':
                await invisible_respond(msg_interaction)
                tokens: float = float(Members.get(id=str(f_interaction.user.id)).tokens)

                if tokens < cash or tokens <= 0:
                    errors += 1
                    if errors < 5:
                        await send_embed(
                            text='That\'s strange. I was checking your balance before.\n'
                                f' But now it\'s less ({tokens}) than the requested amount.\n'
                                ' Please reply with new ECT amount or deposit ECT into your wallet.',
                            color=RED_COLOR,
                            member=f_interaction.user,
                            footer=f'{errors}/5 attempts'
                        )
                    return False
                
                for valut in clan.vault0:
                    if valut.split(":")[0] == str(f_interaction.user.id):
                        valut = valut.split(":")
                        valut[1] = str(float(valut[1]) + cash)
                orm.commit()
                
                member: Members = Members.get(id=str(f_interaction.user.id))

                member.tokens = str(tokens - cash)
                orm.commit()

                await vault0_refresh(clan)

                rate: float = 0
                total_tokens: float = 0
                vault0_tokens: float = 0
                for user in clan.vault0:
                    vault0_tokens += float(user.split(":")[1])
                    if user.split(":")[0] == str(f_interaction.user.id):
                        await send_embed(
                            title='Nice!',
                            text=f'You\'ve topped up city\'s Vault0 with **{cash}** ECT successfully.\n'
                                f'Vault0 share: {user.split(":")[1]} ECT ({user.split(":")[2]}%)',
                            color=GREEN_COLOR,
                            member=f_interaction.user
                        )
                        rate = float(user.split(":")[2])
                        total_tokens = float(user.split(":")[1])

                await send_embed(
                    text=f'{f_interaction.user.mention} topped up our Vault0 for **{cash}** ECT.\n'
                        f'Vault0 balance: **{vault0_tokens}** ECT',
                    color=BLUE_COLOR,
                    channel=f_interaction.guild.get_channel(int(clan.channel_logs_id))
                )

                TransactionMain(
                    type="vault0_top_up",
                    date=datetime.now(),
                    clan=str(clan._id),
                    client=str(f_interaction.user.id),
                    new_total_tokens=str(total_tokens),
                    new_rate=str(rate),
                    new_vault0=str(vault0_tokens),
                )

                await self._log(
                    f"top up clan: {f_interaction.user.id} {f_interaction.user.name}, "
                    f"cash: {cash}, clan: {clan.token}"
                )
                return True


def setup(bot: Bot) -> None:
    bot.add_cog(ClansCog(bot))
    print(f'=== cogs {Clans.__name__} loaded ===')
