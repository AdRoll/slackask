To setup slackask you need to deploy get a slash command token from Slack as well as an incoming webhook url.

Edit the slackask_settings.py file and insert those.  If you'd like to use something other than sqlite also tweak the db url.

Then run pip install -r requirements.txt

Run python application.py and you're off to the races.

Pull requests welcome!