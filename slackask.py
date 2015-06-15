import flask
import requests
import json, re, os
from models import Question, QuestionStatus, UserIndex
import models


app = flask.Flask(__name__)

app.config.from_object('slackask_settings')

# you can override settings by setting environment variables
if 'SLACKASK_SETTINGS' in os.environ:
    app.config.from_envvar('SLACKASK_SETTINGS')


def listForUser(username, status=QuestionStatus.pending):
    if status == QuestionStatus.all:
        return flask.render_template("list_questions.txt", questions=flask.g.db_session.query(Question).filter_by(username=username), status=status, statusEnum=QuestionStatus) + "\n"
    else:
        return flask.render_template("list_questions.txt", questions=flask.g.db_session.query(Question).filter_by(username=username, status=status), status=status, statusEnum=QuestionStatus) + "\n"

def publish(username, question_number, channel, republish=False):
    if republish:
        question = flask.g.db_session.query(Question).filter_by(username=username, number=question_number).first()
    else:
        question = flask.g.db_session.query(Question).filter_by(username=username, status=QuestionStatus.pending, number=question_number).first()
    if question is None:
        return "I didn't find any questions for you with number {}\n".format(question_number), 200
    output = flask.render_template("question.txt", username=username, question=question) + "\n"
    result = sendMessage(('#' + channel) if channel[0] != '#' else channel, output)
    if result.ok:
        question.status=QuestionStatus.published
        flask.g.db_session.add(question)
        return "Question {} published\n".format(question_number), 200
    else:
        return "Problem asking question {}.  Try again later.\n".format(question_number), 500

def delete(username, question_number):
    question = flask.g.db_session.query(Question).filter_by(username=username, status=QuestionStatus.pending, number=question_number).first()
    if question is None:
        return "I didn't find any questions for you with number {}\n".format(question_number), 200
    question.status=QuestionStatus.deleted
    flask.g.db_session.add(question)
    return "Question {} deleted\n".format(question_number), 200

def undelete(username, question_number):
    question = flask.g.db_session.query(Question).filter_by(username=username, status=QuestionStatus.deleted, number=question_number).first()
    if question is None:
        return "I didn't find any questions for you with number {}\n".format(question_number), 200
    question.status=QuestionStatus.pending
    flask.g.db_session.add(question)
    return "Question {} undeleted\n".format(question_number), 200

def sendMessage(channelName, message):
    payload = {"channel": channelName,
               "text": message,
               "username": "SlackAsk",
               "icon_emoji": ":question:"}
    result = requests.post(app.config['SLACKASK_INCOMING_WEBHOOK_URL'], data={"payload": json.dumps(payload)})
    return result

def askUser(username, question_text):
    user_index = flask.g.db_session.query(UserIndex).filter_by(username=username).first()
    if user_index is None:
        user_index = UserIndex(number=1, username=username)
    else:
        user_index.number += 1
    flask.g.db_session.add(user_index)
    question = Question(number=user_index.number, status=QuestionStatus.pending, username=username, question=question_text)
    questionTemplate = flask.render_template("new_question.txt", question=question)
    result = sendMessage('@{}'.format(username), questionTemplate)
    if result.ok:
        flask.g.db_session.add(question)
        return "Asked {} the following question {}\n".format(username, question_text), 200
    else:
        return "Had trouble asking the question to that user.\n", 200


def trimNumber(numberString):
    return numberString[1:] if numberString[0] == '#' else numberString

def routeCommand(commandString, username, channel):
    commandPieces = commandString.split()
    command = commandPieces[0]
    commandArgs = commandPieces[1:]
    if command == "list":
        status = QuestionStatus.pending
        if len(commandArgs) > 0:
            statusName = commandArgs[0]
            status = QuestionStatus.statusForName(statusName)
        return listForUser(username, status)
    elif command == "publish":
        if len(commandArgs) == 2:
            channel = commandArgs[1]
        questionNumber = commandArgs[0]
        return publish(username, trimNumber(commandArgs[0]), channel)
    elif command == "republish":
        if len(commandArgs) == 2:
            channel = commandArgs[1]
        questionNumber = commandArgs[0]
        return publish(username, trimNumber(commandArgs[0]), channel, republish=True)
    elif command == "delete":
        return delete(username, trimNumber(commandArgs[0]))
    elif command == "undelete":
        return undelete(username, trimNumber(commandArgs[0]))
    elif command == "help":
        return flask.render_template("help.txt") + "\n"
    elif len(commandArgs) > 0:
        userToAsk = command
        return askUser(userToAsk[1:] if userToAsk[0] == '@' else userToAsk, re.sub("^{}\s*".format(userToAsk), "", commandString))


@app.route("/", methods=["POST"])
def handleSlackCommand():
    if flask.request.form["token"] != app.config['SLACKASK_TOKEN']:
                       return "Request forbidden\n", 403
    return routeCommand(flask.request.form["text"], flask.request.form["user_name"] if "user_name" in flask.request.form else None, ("#" + flask.request.form["channel_name"]) if "channel_name" in flask.request.form else None)

@app.route("/healthcheck", methods=["GET"])
def healthCheck():
    return "Ok", 200

@app.before_request
def application_setup():
    flask.g.db_session = models.create_db_session(app.config['SLACKASK_DB_URI'])


@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception is not None:
        flask.g.db_session.rollback()
    else:
        flask.g.db_session.commit()
    flask.g.db_session.remove()
