from operator import attrgetter
from typing import Union, Optional, TypeVar, Iterable

import dis_snek
from dis_snek import Snake
from dis_snek.models import Guild, Role, Member, message_command, listen, slash_command, slash_option, \
    InteractionContext, AutocompleteContext, Embed, SelectOption, Select, ActionRow, Button
from dis_snek.models.events import Component, MemberAdd
from dis_snek.models.scale import Scale

# Why if this needed!?
dis_snek.models.Role.__hash__ = dis_snek.models.SnowflakeObject.__hash__


class Team:
    def __init__(self, role: Role):
        self.role = role

    async def join(self, member: Member):
        await member.add_role(self.role, reason='Team change')

    @property
    def members(self) -> list[Member]:
        # members = self.role.guild.members
        # return [member for member in members if member.has_role(self.role)]
        return self.role.members

    @property
    def name(self) -> str:
        return self.role.name

    def __str__(self):
        return self.role.name

    def __repr__(self):
        return f'<Team role={self.role.id} name="{self.name}">'

    def __hash__(self):
        return self.role.__hash__()


class TeamScale(Scale):
    def __init__(self, bot):
        self.bot: Snake = bot
        self.teams: list[Team] = []
        self.guild: Guild

    async def team_autocomplete(self, ctx: AutocompleteContext, team: str):
        teams = [str(team_) for team_ in self.teams
                  if (team_.name.startswith(team) or team_.name.startswith('Team ' + team))]
        await ctx.send(choices=teams)

    # noinspection PyAttributeOutsideInit
    @listen()
    async def on_startup(self):
        assert len(self.teams) == 0

        self.guild = await self.bot.get_guild(910984528351338557)
        for role in self.guild.roles:
            if role.name.startswith('Team '):
                role.guild = self.guild
                self.teams.append(Team(role=role))

        self.alert_role = await self.guild.get_role(916508698698973225)

        # for member in self.guild.members:
        #     if not await member.has_role(self.alert_role):
        #         await member.add_role(self.alert_role)
        #         await asyncio.sleep(5)
        #     print('Member checked')
        # print('Done')

    @listen()
    async def on_member_add(self, member: MemberAdd):
        print('Member added')
        await member.member.add_role(self.alert_role)



    @message_command(name='teams')
    async def teams(self, ctx):
        """Show current teams"""
        await ctx.send(self.teams.__str__())

    @slash_command(name='team',
                   sub_cmd_name='join',
                   description='Join a team')
    @slash_option('team', 'Which team to join', 3, True, True)
    async def join_team(self, ctx: InteractionContext,
                         team: str
                         ):
        team = ' '.join(team.split('_'))

        for team_ in self.teams:
            if team_.name == team:
                break
        else:
            return await ctx.send('That is not a team')

        # noinspection PyUnboundLocalVariable
        await ctx.author.add_role(team_.role)
        await ctx.send(f'You have been added to {team}!')

    join_team.autocomplete('team')(team_autocomplete)

    @slash_command(name='team', sub_cmd_name='create')
    @slash_option('name', 'The name of the team', 3, True)
    async def team_create(self, ctx: InteractionContext, name: str):
        role = await self.guild.create_role('Team ' + name)
        self.teams.append(Team(role=role))
        await ctx.send(f'Team {name} created!')

    # noinspection PyUnboundLocalVariable
    @slash_command(name='team', sub_cmd_name='info')
    @slash_option('team', 'What team you want info about', 3, False, True)
    async def team_info(self, ctx: InteractionContext, team: str = None):
        if team is None:
            msg = ''
            for team_ in self.teams:
                msg += f'**__{team_.name}__**\n'
                # print(team_.members)
                for member in team_.members:
                    msg += member.display_name + '\n'
            # print(msg)
            return await ctx.send(msg)

        team = ' '.join(team.split('_'))

        for team_ in self.teams:
            if team_.name == team:
                break
        else:
            return await ctx.send('That is not a team')

        embed = Embed()
        embed.title = team_.name
        embed.add_field('Members', ', '.join((f'<@{member.id}>' for member in team_.members)) or 'None', inline=False)
        await ctx.send(embeds=[embed])

    team_info.autocomplete('team')(team_autocomplete)

    @slash_command(name='role', sub_cmd_name='select')
    @slash_option('roles', 'The roles you want to give, separated by |. Can be mentions or names', 3, True)
    @slash_option('content', 'What to say above the select', 3, True)
    async def role_select(self, ctx: InteractionContext, roles: str, content: str):
        roles: list[Role] = [
            (
                await get_role(ctx.guild, role)
            )
            for role in roles.split('|')
        ]
        if None in roles:
            # print(roles)
            return await ctx.send('One of the roles was not found!')

        options = [SelectOption(role.name, role.name) for role in roles]
        select = Select(
            options=options,
            custom_id='select_roles',
            min_values=0,
            max_values=len(options),
        )

        await ctx.send('Select created!', ephemeral=True)
        await ctx.channel.send(content=content, components=[ActionRow(select)])

    @slash_command(name='role', sub_cmd_name='button')
    @slash_option('role', 'The role you want to give', 8, True)
    @slash_option('content', 'What to say above the button', 3, True)
    async def role_button(self, ctx: InteractionContext, role: Role, content: str):
        # role = await get_role(ctx.guild, role)
        # if role is None:
        #     return await ctx.send('No role found')

        button = Button(label=role.name, style=1, custom_id='button_role')

        await ctx.send('Button Created', ephemeral=True)
        await ctx.channel.send(
            content=content,
            components=[ActionRow(button)],
        )

    @listen()
    async def on_component(self, event: Component):
        ctx = event.context

        # # print(dir(ctx))

        # for item in dir(ctx):
        #     if not item.startswith('__'):
        #         print(f'{item}: {getattr(ctx, item)}')
        # print(ctx.data['data']['values'])
        #       # ['values'])

        if ctx.custom_id == 'select_roles':
            options = ctx.data['message']['components'][0].components[0].options

            all_roles = {
                get(ctx.guild.roles, name=option['value'])
                for option in options
            }

            to_add = {
                get(ctx.guild.roles, name=option)
                for option in ctx.values
            }
            to_remove = all_roles - to_add

            # print(to_add)

            [await ctx.author.add_role(role) for role in to_add]
            [await ctx.author.remove_role(role) for role in to_remove]

            await ctx.send('Roles changed!', ephemeral=True)

        elif ctx.custom_id == 'button_role':
            role = get(ctx.guild.roles, name=ctx.data['message']['components'][0].components[0].label)

            if role in ctx.author.roles:
                await ctx.author.remove_role(role)
            else:
                await ctx.author.add_role(role)

            await ctx.send('Roles changed!', ephemeral=True)

def setup(bot):
    TeamScale(bot)


_T = TypeVar('_T')
def get(iterable: Iterable[_T], **attrs) -> Optional[_T]:

    _all = all
    attrget = attrgetter

    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace('__', '.'))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace('__', '.')), value)
        for attr, value in attrs.items()
    ]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None

async def get_role(guild: Guild, id_or_name: Union[int, str]) -> Optional[Role]:
    if isinstance(id_or_name, int) or id_or_name.isnumeric():
        return await guild.get_role(id_or_name)
    else:
        if id_or_name.startswith('<@&') and id_or_name.endswith('>') and id_or_name[2:-1].isdigit():
            return await guild.get_role(id_or_name[2:-1])
        return get(guild.roles, name=id_or_name)