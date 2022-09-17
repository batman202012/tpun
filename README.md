<div id="header" align="center">

 <img src="https://i.imgur.com/1heyRLg.gif"/>

</div>

<div id="socials" align="center">

[![Discord](https://img.shields.io/badge/Discord-blue?style=flat&logo=Discord&logoColor=white)](https://discordapp.com/users/365398642334498816) [![Youtube](https://img.shields.io/badge/Youtube-red?style=flat&logo=Youtube&logoColor=white)](https://www.youtube.com/channel/UCFu5oVPzFrSk5HhkPhgeRhQ) [![Linkedin](https://img.shields.io/badge/Linkedin-blue?style=flat&logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/joseph-m-b48b66136/) [![Steam](https://img.shields.io/badge/Steam-gray?style=flat&logo=Steam&logoColor=white)](https://steamcommunity.com/id/sgtnado/) 

</div>

<div id="Instalalation" align="center">

# Team Punistic Cogs

<div id="workflow" align="center">

[![Python application](https://github.com/batman202012/tpun/actions/workflows/main.yml/badge.svg?branch=beta-testing)](https://github.com/batman202012/tpun/actions/workflows/main.yml) [![CodeQL](https://github.com/batman202012/tpun/actions/workflows/codeql-analysis.yml/badge.svg?branch=beta-testing)](https://github.com/batman202012/tpun/actions/workflows/codeql-analysis.yml)[![Requirements Status](https://requires.io/github/batman202012/tpun/requirements.svg?branch=beta-testing)](https://requires.io/github/batman202012/tpun/requirements/?branch=beta-testing)[![Maintainability](https://api.codeclimate.com/v1/badges/ccf09712a5af256e1fc6/maintainability?branch=beta-testing)](https://codeclimate.com/github/batman202012/tpun/maintainability)

</div>

<br />
<br />

## Installation

<br />

</div>

- `
[p] is your prefix
`



<br />

1. `
[p]repo add tpun https://github.com/batman202012/tpun
`

<br />

2. `
[p]cog install tpun <cog-folder-name>
`

<br />

3. `
[p]load <cog-folder-name>
`

<br />


<div id="coglist" align="center">

## Cog list

<br />

</div>

- [Private Voice Channels](#pvc)

<br />

- [Reputation](#rep)

<br />

- [Role Buy](#rolebuy)

<br />

- [Usergate](#usergate)

<br />

- [Verifier](#verifier)

<br />

- [PingEveryone](#pingeveryone)

<br />

- [ServerHud](#serverhud)

<br />
<br />

<div id="pvc" align="center">

## PVC 



<br />

### Cog for creating private voice channels

</div>

<div align="right">

[top](#coglist)

</div>

<br /> 

- `
[p]vc setup
`

##### Creates command channel for pvc and selects the channel's default joinable role (used for lock/unlock)

<br />
<br />

- `
[p]vc create <name>
`


##### Creates a voice channel in the catergory the pvc command channel is in with name 'name'

<br />
<br />

- `
[p]vc delete
`

##### Deletes your private voice channel

<br />
<br />  

- `
[p]vc name
`

##### Returns the name of your private voice channel

<br />
<br />

- `
[p]vc list
`

##### Returns an embed of personal voice channel and owners

<br />
<br />

- `
[p]vc rename <name>
`

##### Renames your private voice channel to 'name'

<br />
<br />

- `
[p]vc region <int>
`

##### Changes your private voice channel region to 'int'
###### The list of avaliable regions are as follow 0=Auto, 1=US West, 2=US East, 3=US South, 4=EU West, 5=EU Central, 6=Brazil, 7=Hong Kong, 8=Brazil, 9=Japan, 10=Russia, 11=Sydney, 12=South Africa

<br />
<br /> 

- `
[p]vc lock
`

##### Prevents the roles used in vc setup from joining the channel

<br />
<br /> 

- `
[p]vc unlock
`

##### Allows the roles used in vc setup to join the channel

<br />
<br /> 

- `
[p]vc invite <user mention>
`

##### Invites a 'user' to join your private voice channel

<br />
<br /> 
<h5>

- `
[p]vc limit <int>
`

##### Sets the user limit as 'int' for your private voice channel, use 0 to set it to uncapped
<br />
<br /> 

- `
[p]vc request <user mention>
`

##### Requests to join "user"'s private voice channel, only works when used on the channel's owner

<br />
<br />
  
- `
[p]vc kick <user mention>
`

##### Kicks 'user' from your private voice channel and removes their permissions to join

<br />
<br />
  

- `
[p]vc mute <user mention>
`

##### Disables "user"'s permissions to speak/stream/use camera/type in vc text chat in your private voice channel

<br />
<br />

- `
[p]vc unmute <user mention>
`

##### Enables "user"'s permissions to speak/stream/use camera/type in vc text chat in your private voice channel

<br />
<br />
  
- `
[p]vc claim
`

##### Claims a private voice channel as yours if the owner is no longer present

<br />
<br />

- `
[p]vc transfer <user mention>
`

##### Transfers private voice channel ownership to 'user'

<br />
<br />

- `
[p]vc setup
`

##### Command for setting up private voice channels in the server

<br />
<br />

<div id="rep" align="center">

## Reputation

</div>

<br />

### Gives users +1 rep everytime someone thanks them

<div align="right">

[top](#coglist)

</div>

<br />

- `
[p]repremove <user mention> <amount to remove>
`

##### Removes 'amount' of reputation from 'user'

<br />
<br />  

- `
[p]checkrep <user mention>
`

##### Checks the amount of rep 'user' has

<br />
<br />

<div id="rolebuy" align="center">

## Rolebuy

<br />

### Allows users to buy roles using redbot currency

</div>

<div align="right">

[top](#coglist)

</div>

<br />

- `
[p]rb buy <role mention>
`

##### Buys 'role' and removes currency from user

<br />
<br />

- `
[p]rb add <role mention> <cost>
`

##### Adds 'role' to list of buyable roles for 'cost'

<br />
<br />

- `
[p]rb remove <role mention>
`

##### Removes 'role' from buyable roles

<br />
<br />

- `
[p]rb list
`

##### Lists the available buyable roles in server

<br />
<br />

<div id="usergate" align="center">

## Usergate

<br />

### Prevents user accounts that are under 'days' old from joining the server

<br />

</div>

<div align="right">

[top](#coglist)

</div>

<br /> 

- `
[p]usergate <days>
`

##### Sets the number of 'days' a user's account must exist

<br />
<br />

<div id="verifier" align="center">

## Verifier

<br />

### Verifies users as a gender role using a gui

</div>

<div align="right">

[top](#coglist)

</div>

<br /> 

- `
[p]verify <user mention>
`

##### Removes 'user' unverified role and gives them their selected (from gui) verified role

<br />
<br />

- `
[p]vsetup
`

##### set the male, female, non-binary and unverified roles to use for verification

<div id="pingeveryone" align="center">

## Pingeveryone

<br />

### Just a simple cog that adds a command to ping @everyone and @here

</div>

<div align="right">

[top](#coglist)

</div>

<br /> 

- `
[p]pingeveryone
`

##### Allows users with bot admin perms to ping everyone

<br />
<br />

- `
[p]pinghere
`

##### Allows users with bot admin perms to ping here

<br />
<br />

<div id="serverhud" align="center">

## Server Hud

<br />

### A Cog for creating customizable voice channel stats

</div>

<div align="right">

[top](#coglist)

</div>

<br /> 

- `
[p]serverhud setchannel <type> <channel id>
`

##### Sets 'channel id' to be the serverhud 'type'

<br />
<br />

- `
[p]serverhud types
`

##### Lists the types of avaliable server hud

<br />
<br />

- `
[p]serverhud setprefix <type> <prefix>
`

##### Sets channel 'type' to have the 'prefix'

<br />
<br />

- `
[p]serverhud setsuffix <type> <suffix>
`

##### Sets channel 'type' to have the 'suffix'

<br />
<br />

- `
[p]serverhud setname <type> <name>
`

##### Sets channel 'type' to have the 'name'

<br />
<br />

- `
[p]serverhud setstyle <type> <style>
`

##### Sets the booster bar to use 'style' for either type: 'empty' or 'full'
##### ex: full * empty -: with 6 boosts = Lvl1******-

<br />
<br />

- `
[p]serverhud test <event>
`

##### Tests the serverhud for various events 'join' and 'leave'

<br />
<br />
