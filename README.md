To setup slackask you need to deploy get a slash command token from Slack as well as an incoming webhook url.
Edit the slackask_settings.py file and insert those.  If you'd like to use something other than sqlite also tweak the db url.

Then run ```$ pip install -r requirements.txt```

Run ```$ python application.py``` and you're off to the races.

When you're off to the races you can use it from slack like so:

```
/ask @phuff What is your favorite color?
```

@phuff can then post the question if they so choose:

```
/ask publish 1 #my-favorite-channel-name
```

If they don't want to publish it they can delete it:

```
/ask delete 1
```

Users can list the questions they've been asked:
```
/ask list
```

And help is always a command away:

```
/ask help
```

Pull requests welcome!
