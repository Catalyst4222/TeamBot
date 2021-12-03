import asyncio
from dis_snek import Snake
from dis_snek.models import Guild, Role, Member, message_command, listen, slash_command, slash_option, \
    InteractionContext, AutocompleteContext, Embed
from dis_snek.models.events import Component
from dis_snek.models.scale import Scale
from operator import attrgetter

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
        self.groups: list[Team] = []
        self.guild: Guild

    async def group_autocomplete(self, ctx: AutocompleteContext, group: str):
        groups = [str(group_) for group_ in self.groups
                  if (group_.name.startswith(group) or group_.name.startswith('Team ' + group))]
        await ctx.send(choices=groups)

    # noinspection PyAttributeOutsideInit
    @listen()
    async def on_startup(self):
        assert len(self.groups) == 0

        self.guild = await self.bot.get_guild(910984528351338557)
        for role in self.guild.roles:
            if role.name.startswith('Team '):
                role.guild = self.guild
                self.groups.append(Team(role=role))

    @message_command(name='groups')
    async def groups(self, ctx):
        """Show current groups"""
        await ctx.send(self.groups.__str__())

    @slash_command(name='group',
                   sub_cmd_name='join',
                   description='Join a group')
    @slash_option('group', 'Which group to join', 3, True, True)
    async def join_group(self, ctx: InteractionContext,
                         group: str
                         ):
        group = ' '.join(group.split('_'))

        for group_ in self.groups:
            if group_.name == group:
                break
        else:
            return await ctx.send('That is not a group')

        # noinspection PyUnboundLocalVariable
        await ctx.author.add_role(group_.role)
        await ctx.send(f'You have been added to {group}!')

    join_group.autocomplete('group')(group_autocomplete)

    @slash_command(name='group', sub_cmd_name='create')
    @slash_option('name', 'The name of the group', 3, True)
    async def group_create(self, ctx: InteractionContext, name: str):
        role = await self.guild.create_role('Team ' + name)
        self.groups.append(Team(role=role))
        await ctx.send(f'Team {name} created!')

    # noinspection PyUnboundLocalVariable
    @slash_command(name='group', sub_cmd_name='info')
    @slash_option('group', 'What group you want info about', 3, False, True)
    async def group_info(self, ctx: InteractionContext, group: str = None):
        if group is None:
            msg = ''
            for group_ in self.groups:
                msg += f'**__{group_.name}__**\n'
                print(group_.members)
                for member in group_.members:
                    msg += member.display_name + '\n'
            # print(msg)
            return await ctx.send(msg)

        group = ' '.join(group.split('_'))

        for group_ in self.groups:
            if group_.name == group:
                break
        else:
            return await ctx.send('That is not a group')

        embed = Embed()
        embed.title = group_.name
        embed.add_field('Members', ', '.join((f'<@{member.id}>' for member in group_.members)) or 'None', inline=False)
        await ctx.send(embeds=[embed])

    group_info.autocomplete('group')(group_autocomplete)


    @cog_subcommand(
        base='role',
        subcommand_group='add',
        name='select',
        description='Make a select that gives roles',
        options=[
            {
                'name': 'roles',
                'description': 'The roles you want to give, separated by |. Can be mentions or names',
                'required': True,
                'type': 3,
            },
            {
                'name': 'create_roles',
                'description': 'Whether to create any missing roles',
                'required': False,
                'type': 5,
            },
        ],
    )
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    async def role_select(self, ctx: InteractionContext, roles: str, create_roles: bool = False):
        try:
            roles: list[Role] = [
                (
                    await utils.get_or_make_role(ctx, role)
                    if create_roles
                    else await commands.RoleConverter().convert(ctx, role)
                )
                for role in roles.split('|')
            ]
            if None in roles:
                raise commands.RoleNotFound

        except commands.RoleNotFound:
            return await ctx.send('One or more roles failed to convert')

        options = [create_select_option(role.name, role.name) for role in roles]
        select = create_select(
            options=options,
            custom_id='select_roles',
            min_values=0,
            max_values=len(options),
        )

        await ctx.send('Choose your roles here:', components=[create_actionrow(select)])

    @listen()
    async def on_component(self, event: Component):
        ctx = event.context

        if ctx.custom_id == 'select_roles':

            all_roles = {
                get(ctx.guild.roles, name=option['value'])
                for option in ctx.component['options']
            }
            to_add = {
                get(ctx.guild.roles, name=option)
                for option in ctx.selected_options
            }
            to_remove = all_roles - to_add

            await ctx.author.add_roles(*to_add)
            await ctx.author.remove_roles(*to_remove)

            await ctx.send('Roles changed!', ephemeral=True)

def setup(bot):
    TeamScale(bot)

def get(iterable, **attrs):
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