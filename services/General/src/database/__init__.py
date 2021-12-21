from datetime import datetime

from pony.orm import *

db = Database()


class Members(db.Entity):
    _id = PrimaryKey(int, auto=True)
    id = Optional(str)
    name = Optional(str)
    created_at = Optional(datetime)
    verification_owner_servers = Optional(StrArray)
    total_count_sends_mark_local = Optional(str)
    total_costs_for_mark_global = Optional(str)
    ether_status = Optional(bool)
    nods_status = Optional(bool)
    vi0_status = Optional(bool)
    vi1_status = Optional(bool)
    exp_all = Optional(str)
    exp_rank = Optional(str)
    lvl_rank = Optional(str)
    tokens = Optional(str)
    daily_exp_msg_limit = Optional(str)
    daily_exp_msg_limit_time = Optional(str)
    wallet = Optional(str)
    clans_id = Optional(StrArray)


class Guilds(db.Entity):
    _id = PrimaryKey(int, auto=True)
    id = Optional(str)
    name = Optional(str)
    created_at = Optional(datetime)
    owner = Optional(str)
    owner_id = Optional(str)
    occasion_creating_clan=Optional(bool)
    role_nods = Optional(str)
    role_ether = Optional(str)
    msg_rating_id = Optional(str)
    msg_wallet_id = Optional(str)
    frozen = Optional(bool)
    main_server = Optional(bool)
    verification = Optional(bool)
    system_ch_category = Optional(str)
    system_ch_city_setup = Optional(str)
    system_ch_city_setup_msg = Optional(str)
    system_ch_help = Optional(str)
    clans = Optional(StrArray)


class Ethers(db.Entity):
    _id = PrimaryKey(int, auto=True)
    owner_id = Optional(str)
    name = Optional(str)
    token = Optional(str)
    status_clan = Optional(bool)
    _id_clan = Optional(str)
    _id_guild = Optional(str)
    guild_id = Optional(str)


class Clans(db.Entity):
    _id = PrimaryKey(int, auto=True)
    owner_clan = Optional(str)
    guild = Optional(str)
    name = Optional(str)
    token = Optional(str)
    invite_link = Optional(str)
    ether_id = Optional(str)
    frozen = Optional(bool)
    category_id = Optional(str)
    msg_statistics_id = Optional(str)
    msg_join_id = Optional(str)
    msg_wallet_id = Optional(str)
    msg_marketplace_id = Optional(str)
    channel_join_id = Optional(str)
    channel_engage_id = Optional(str)
    channel_marketplace_id = Optional(str)
    channel_wallet_id = Optional(str)
    channel_statistics_id = Optional(str)
    channel_logs_id = Optional(str)
    channel_help_id = Optional(str)
    channel_voice_id = Optional(str)
    role_owner_id = Optional(str)
    role_nods_id = Optional(str)
    role_support_id = Optional(str)
    color_clan = Optional(str)
    total_exp = Optional(str)
    vault0 = Optional(StrArray)
    vault1 = Optional(str)
    total_income_from_mark_global = Optional(str)
    total_exp = Optional(str)
    other_channels = Optional(StrArray)
    nods = Optional(StrArray)
    supports = Optional(StrArray)
    history_nods = Optional(StrArray)
    history_supports = Optional(StrArray)
    members_rating = Optional(StrArray)


class SmartContracts(db.Entity):
    _id = PrimaryKey(int, auto=True)
    clan_id = Optional(str)
    contracts = Optional(Json)


class RatingClans(db.Entity):
    _id = PrimaryKey(int, auto=True)
    clan_id = Optional(str)
    token = Optional(str)
    name = Optional(str)
    invite_link = Optional(str)
    channel_statistics_id = Optional(str)
    msg_statistics_id = Optional(str)
    guild = Optional(str)
    members = Optional(StrArray)
    supports = Optional(StrArray)
    members_count = Optional(str)
    total_exp = Optional(str)
    clan_rate = Optional(str)
    last_list = Optional(StrArray)


class TransactionMain(db.Entity):
    _id = PrimaryKey(int, auto=True)
    type = Optional(str)
    date = Optional(datetime)
    from_user = Optional(str)
    from_clan = Optional(str)
    to_channel = Optional(str)
    to_user = Optional(str)
    link = Optional(str)
    msg_id = Optional(str)
    sum = Optional(str)
    clan = Optional(str)
    client = Optional(str)
    new_total_tokens = Optional(str)
    new_rate = Optional(str)
    new_vault0 = Optional(str)
    received_tokens = Optional(str)
    rate = Optional(str)
    vault1 = Optional(str)
    user_id = Optional(str)
    get_tokens = Optional(str)
    new_lvl = Optional(str)
    guild = Optional(str)
    owner = Optional(str)
    clans = Optional(StrArray)


class MarkGlobal(db.Entity):
    _id = PrimaryKey(int, auto=True)
    user_id = Optional(str)
    to_clans = Optional(StrArray)
    msg_list = Optional(StrArray)
    from_clan = Optional(str)
    link = Optional(str)
    date = Optional(datetime)


class CheckBusy(db.Entity):
    _id = PrimaryKey(int, auto=True)
    names = Optional(StrArray)
    status = Optional(str)
    incs = Optional(str)
    tokens = Optional(StrArray)
    incs_escrow = Optional(str)
    total_give_tokens = Optional(str)


class WhiteListUsers(db.Entity):
    _id = PrimaryKey(int, auto=True)
    id = Optional(str)
    name = Optional(str)


db.bind(
    provider='postgres', user='vlozfopocbvhgz', 
    password='96cf51400190f177001ea18e21213309bb8516a265a2b55e4e11bef0dc3d54d4', 
    database='d5ukqrppc8dn6a', host='ec2-52-21-193-223.compute-1.amazonaws.com',
    port=5432
)
db.generate_mapping(create_tables=True, check_tables=True)
