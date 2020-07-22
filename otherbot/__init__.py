from redbot.core.errors import CogLoadError


async def setup(bot):
    raise CogLoadError(
        "This fork of otherbot has been deprecated as it as been merged to aikaterna's repository.\n\n"
        "Steps to migrate (repo_name is the name of repo you've set when adding this repo):\n"
        "1. `[p]cog uninstall otherbot`\n"
        "2. `[p]repo delete repo_name`\n"
        "3. `[p]repo add aikaterna https://github.com/aikaterna/aikaterna-cogs`\n"
        "4. `[p]cog install aikaterna otherbot`\n"
        "5. `[p]load otherbot`\n\n"
        "**Your data will __not__ be lost by moving to this repo.**"
    )
