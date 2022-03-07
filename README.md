# laffey-bot
discord bot with valorant commands

## valorant commands
valorant-setchannel
> sets the current channel of the server for the bot to send updates to

valorant-info
> retrives the user's saved info from the playerData.json database.
> > - in game name
> > - in game tag
> > - latest time - time when user is added, changes to most recent played game  

valorant-watch <name\> <tag\>
> adds the discord user to the playerData.json database. the bot will send an embed when it detects the user has completed a game.  
> > - in game name
> > - in game tag
> > - riot PUUID
> > - latest time - time when user is added, changes to most recent played game

valorant-unwatch
> removes the user from the playerData.json database. the bot will stop watching for the user's games.


valorant-wait *<wait_user\>
> pings the user when the bot has detected the wait_user has completed a game. wait_user must be currently watched and in database.\
> for the prefix command, multiple users can be tagged in the command

valorant-waitlist
> returns an embed with the current waiting list. shows each wait_users and the users waiting for them.

## how to setup
### config.json
note: config.json will be removed eventually
guilds
> int[]: list of guild IDs, IDs are integers. used for debugging when changing or adding slash-commands (as it takes time to sync). remove guild-ids from each slash-command for global use (but will take time to update).

feeder_embed_image
> str[]: list of urls for the feeder embed image. the bot will randomly choose 1 from the list each time.

### .env
BOT_TOKEN
> place your Discord Application token in here.

RIOT_TOKEN
> place your Riot API key in here. (currently unused at the moment)

HOLODEX_TOKEN
> place your [Holodex](https://holodex.net/) API key in here.

DEFAULT_PREFIX
> place the prefix the bot will default to when joining a new server

SLASH_ENABLED
> int: 1 or 0. 1 to enable [slash-commands](https://discord.com/blog/slash-commands-are-here), 0 to disable.

PREFIX_ENABLED
> int: 1 or 0. 1 to enable prefixed commands, 0 to disable.