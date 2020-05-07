# Copyright (C) 2020 Adek Maulana.
# All rights reserved.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#

"""
   Heroku manager for your userbot
"""

import heroku3
import os
import requests
import math

from userbot import CMD_HELP, HEROKU_APP_NAME, HEROKU_API_KEY
from userbot.events import register
from userbot.utils.prettyjson import prettyjson

Heroku = heroku3.from_key(HEROKU_API_KEY)
heroku_api = "https://api.heroku.com"

@register(pattern="^.hlist(?: |$)(.*)", outgoing=True)
async def heroku_list(list):
    """ Getting Information From Heroku Account """
    
    if list.is_channel and not list.is_group:
        await list.edit("`hlist isn't permitted on channels`")
        return
    if HEROKU_API_KEY is not None:
        heroku_str = list.pattern_match.group(1)
        if heroku_str == "app":
            applist = str(heroku_conn.apps(order_by='id'))
            plist = applist.replace("[<app '", "").replace("<app '", "").replace("'>,", "\n\n").replace("'>]", "")
            await list.edit(f"**List App on Your Account:**\n\n`{plist}`")
        elif heroku_str == "worker":
            if HEROKU_APP_NAME is not None:
                app = heroku_conn.apps()[HEROKU_APP_NAME]
                dynolist = str(app.dynos(order_by='id'))
                dlist = dynolist.replace("[<Dyno '", "").replace("<Dyno '", "").replace("'>,", "\n\n").replace("'>]", "")
                await list.edit(f"**List Worker on Your {HEROKU_APP_NAME}:**\n\n{dlist}")
            else:
                await list.edit("Please setup your **HEROKU_APP_NAME** Config Variable")
        elif heroku_str == "var":
            if HEROKU_APP_NAME is not None:
                app = heroku_conn.apps()[HEROKU_APP_NAME]
                config = str(app.config())
                vlist = config.replace(",", "\n\n").replace("'", "`").replace("{", "").replace("}", "")
                if BOTLOG:
                    await list.edit(f"List of `Config Variable` has been sent to your `BOTLOG Group`")
                    await list.client.send_message(BOTLOG_CHATID, (f"**List Config Variable on Your {HEROKU_APP_NAME}:**\n\n{vlist}"))
                else:
                    await list.edit(f"Sorry, Can't send `Config Variable` to Public.\nPlease setup your **BOTLOG Group**")
            else:
                await list.edit("Please setup your **HEROKU_APP_NAME** Config Variable")
        else:
            await list.edit("Please enter valid command\nSee `.help heroku`")
    else:
        await list.edit("Please setup your **HEROKU_API_KEY** Config Variable")

@register(outgoing=True, pattern=r"^.(set|get|del) var(?: |$)(.*)(?: |$)([\s\S]*)")
async def variable(var):
    """
        Manage most of ConfigVars setting, set new var, get current var,
        or delete var...
    """
    """ Manage most of ConfigVars setting, set new var, or delete var... """
    if var.is_channel and not var.is_group:
        await var.edit("`Heroku Set isn't permitted on channels`")
        return
    if HEROKU_APP_NAME is not None:
        app = Heroku.app(HEROKU_APP_NAME)
    else:
        return await var.edit("`[HEROKU]:"
                              "\nPlease setup your` **HEROKU_APP_NAME**.")
    exe = var.pattern_match.group(1)
    heroku_var = app.config()
    if exe == "get":
        await var.edit("`Getting information...`")
        try:
            variable = var.pattern_match.group(2).split()[0]
            if variable in heroku_var:
                return await var.edit("**ConfigVars**:"
                                      f"\n`{variable}` = `{heroku_var[variable]}`.\n")
            else:
                return await var.edit("**ConfigVars**:"
                                      f"\n`Error > {variable} don't exists`.")
        except IndexError:
            configs = prettyjson(heroku_var.to_dict(), indent=2)
            with open("configs.json", "w") as fp:
                fp.write(configs)
            with open("configs.json", "r") as fp:
                result = fp.read()
                if len(result) >= 4096:
                    await var.client.send_file(
                        var.chat_id,
                        "configs.json",
                        reply_to=var.id,
                        caption="`Output too large, sending it as a file`.",
                    )
                else:
                    await var.edit("`[HEROKU]` ConfigVars:\n\n"
                                   "================================"
                                   f"\n```{result}```\n"
                                   "================================"
                                   )
            os.remove("configs.json")
            return
    elif exe == "set":
        await var.edit("`Setting information...`")
        variable = var.pattern_match.group(2)
        if not variable:
            return await var.edit(">`.set var <ConfigVars-name> <value>`")
        value = var.pattern_match.group(3)
        if not value:
            variable = variable.split()[0]
            try:
                value = var.pattern_match.group(2).split()[1]
            except IndexError:
                return await var.edit(">`.set var <ConfigVars-name> <value>`")
        if variable in heroku_var:
            await var.edit(f"**{variable}** `successfully changed to` > **{value}**")
        else:
            await var.edit(f"**{variable}** `successfully added with value` > **{value}**")
        heroku_var[variable] = value
    elif exe == "del":
        await var.edit("`Getting information to deleting variable...`")
        try:
            variable = var.pattern_match.group(2).split()[0]
        except IndexError:
            return await var.edit("`Please specify ConfigVars you want to delete`.")
        if variable in heroku_var:
            await var.edit(f"**{variable}** `successfully deleted`.")
            if BOTLOG:
                await var.client.send_message(
                    BOTLOG_CHATID, "#DELCONFIGVAR\n\n"
                    "**Delete ConfigVar**:\n"
                    " -> `Config Variable`:\n"
                    f"     • `{variable}`\n\n"
                    "`Successfully deleted...`"
                )
            await var.edit("`Information deleted...`")
            del heroku_var[variable]
        else:
            return await var.edit(f"**{variable}** `is not exists`.")


@register(outgoing=True, pattern=r"^.usage(?: |$)")
async def dyno_usage(dyno):
    """
        Get your account Dyno Usage
    """
    await dyno.edit("`Getting Information...`")
    useragent = ('Mozilla/5.0 (Linux; Android 10; SM-G975F) '
                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                 'Chrome/80.0.3987.149 Mobile Safari/537.36'
                 )
    user_id = Heroku.account().id
    headers = {
     'User-Agent': useragent,
     'Authorization': f'Bearer {HEROKU_API_KEY}',
     'Accept': 'application/vnd.heroku+json; version=3.account-quotas',
    }
    path = "/accounts/" + user_id + "/actions/get-quota"
    r = requests.get(heroku_api + path, headers=headers)
    if r.status_code != 200:
        return await dyno.edit("`Error: something bad happened`\n\n"
                               f">.`{r.reason}`\n")
    result = r.json()
    quota = result['account_quota']
    quota_used = result['quota_used']

    """ - Used - """
    remaining_quota = quota - quota_used
    percentage = math.floor(remaining_quota / quota * 100)
    minutes_remaining = remaining_quota / 60
    hours = math.floor(minutes_remaining / 60)
    minutes = math.floor(minutes_remaining % 60)

    """ - Current - """
    App = result['apps']
    try:
        App[0]['quota_used']
    except IndexError:
        AppQuotaUsed = 0
        AppPercentage = 0
    else:
        AppQuotaUsed = App[0]['quota_used'] / 60
        AppPercentage = math.floor(App[0]['quota_used'] * 100 / quota)
    AppHours = math.floor(AppQuotaUsed / 60)
    AppMinutes = math.floor(AppQuotaUsed % 60)

    return await dyno.edit("**Dyno Usage**:\n\n"
                           f" -> `Dyno usage for`  **{HEROKU_APP_NAME}**:\n"
                           f"     •  `{AppHours}`**h**  `{AppMinutes}`**m**  "
                           f"**|**  [`{AppPercentage}`**%**]\n"
                           "------------------------------------------------------\n"
                           " -> `Dyno hours quota remaining this month`:\n"
                           f"     •  `{hours}`**h**  `{minutes}`**m**  "
                           f"**|**  [`{percentage}`**%**]"
                           )
    Apps = result['apps']
    for apps in Apps:
        if apps.get('app_uuid') == app.id:
            AppQuotaUsed = apps.get('quota_used') / 60
            AppPercentage = math.floor(apps.get('quota_used') * 100 / quota)
            break
        else:
            continue
    try:
        AppQuotaUsed
        AppPercentage
    except NameError:
        AppQuotaUsed = 0
        AppPercentage = 0

    AppHours = math.floor(AppQuotaUsed / 60)
    AppMinutes = math.floor(AppQuotaUsed % 60)

    return await dyno.edit(
         "**Dyno Usage**:\n\n"
         f" -> `Dyno usage for`  **{app.name}**:\n"
         f"     •  `{AppHours}`**h**  `{AppMinutes}`**m**  "
         f"**|**  [`{AppPercentage}`**%**]"
         "\n\n"
         " -> `Dyno hours quota remaining this month`:\n"
         f"     •  `{hours}`**h**  `{minutes}`**m**  "
         f"**|**  [`{percentage}`**%**]"
    )


CMD_HELP.update({
    "heroku":
    ".usage"
    "\nUsage: Check your heroku dyno hours remaining"
    "\n\n.set var <NEW VAR> <VALUE>"
    "\nUsage: add new variable or update existing value variable"
    "\n!!! WARNING !!!, after setting a variable the bot will restarted"
    "\n\n.get var or .get var <VAR>"
    "\nUsage: get your existing varibles, use it only on your private group!"
    "\nThis returns all of your private information, please be caution..."
    "\n\n.del var <VAR>"
    "\nUsage: delete existing variable"
    "\n!!! WARNING !!!, after deleting variable the bot will restarted"
})