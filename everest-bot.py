import telebot
from telebot import types
import requests
import json
import datetime
import time


# Чтобы изменить время для выдачи новых проектов изменить параметр hours
hours = 24
seconds = hours * 60 * 60
now = int(time.time())
# Input bot token
bot = telebot.TeleBot("BOT-TOKEN")


def export(query):
    req = requests.post('https://api.thegraph.com/subgraphs/name/graphprotocol/everest', json={'query': query})
    return json.loads(req.text)

def get_profile(id):
    request = requests.get(f'https://ipfs.3box.io/profile?address={id}')
    try:
        return request.json()['name']
    except:
        return 'Unknown'


def projects():
    query = """query {
      projects(first:1000){
        id
        name
        createdAt
        currentChallenge {
          id
        }
        owner {
          id
        }
      }
    }"""
    return export(query)


def challenged_projects():
    query = """query {
          challenges (where: {resolved: false} ) {
            project {
              id
              name
              createdAt
              owner{
                id
              }
            }
          }
        }"""
    return export(query)


def user_projects(id):
    query = """query {
        projects(where: {owner: """+id+"""}) {
          name,
          id,
          currentChallenge{
            id
          }
          createdAt,
        }
      }"""
    return export(query)

def user_chellange(id):
    query = """query {
        projects(where: {owner: """+id+"""}){
          votes{
            challenge{
              project{
              id
              name
              },
            resolved,
            description,
            },
            choice
          }
        }
      }"""
    return export(query)






default_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
default_markup.add(
    types.KeyboardButton('Project search 🔍'),
    types.KeyboardButton('Owner ID search 👓'),
    types.KeyboardButton('New projects 🔥'),
    types.KeyboardButton('Challenged projects 🏁'),
)

back_markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
back_markup.add(
    types.KeyboardButton('Back')
)




def get_new_projects(time):
    data = projects()
    data = data['data']['projects']

    result = []

    for elem in data:
        if time - elem['createdAt'] <= seconds:
            result.append(elem)

    return result


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Hello! Choose what I need to do!", reply_markup=default_markup)


@bot.message_handler(content_types=['text'])
def text(message):
    if (message.text == 'Project search 🔍'):
        back_markup = types.ForceReply(selective=True)
        bot.send_message(message.chat.id, "Input project name:", reply_markup=back_markup)

    if (message.text == 'Owner ID search 👓'):
        back_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_ffc = types.KeyboardButton("✅ User votes by ID")
        btn_ops = types.KeyboardButton("👓 Owner project by ID")
        back_markup.add(btn_ffc)
        back_markup.add(btn_ops)
        bot.send_message(message.chat.id, "Please, select button", reply_markup=back_markup)
    if (message.text == "✅ User votes by ID"):
        back_markup = types.ForceReply(selective=False)
        bot.send_message(message.chat.id, "Input ID for search:", reply_markup=back_markup)
    if (message.text == "👓 Owner project by ID"):
        back_markup = types.ForceReply(selective=False)
        bot.send_message(message.chat.id, "Input owner ID:", reply_markup=back_markup)
    if (message.text == 'Find from challanges'):
        back_markup = types.ForceReply(selective=True)
        bot.send_message(message.chat.id, "Input ID for search:", reply_markup=back_markup)
    if message.text == 'Challenged projects 🏁':
        data = challenged_projects()
        try:
            data = data['data']['challenges']
            result = []
            for elem in data:
                result.append(elem['project'])
            count = len(result)
            if count > 0:
                bot.send_message(message.chat.id, f"ℹ Found <b>{count}</b> projects",
                                 reply_markup=default_markup, parse_mode='HTML')
                counter = 1
                for project in result:
                    time = datetime.datetime.fromtimestamp(float(project['createdAt']))
                    owner_name = get_profile(project['owner']['id'])
                    if owner_name == "Unknown":
                        bot.send_message(message.chat.id,
                                         f"<b>{counter}</b>. <a href=\"https://everest.link/project/{project['id']}\">{project['name']}</a>\nAdded: {time:%d.%m.%y %H:%M}\nOwner ID: <b>{project['owner']['id']}</b>",
                                         reply_markup=default_markup, parse_mode='HTML',
                                         disable_web_page_preview=True)
                    else:
                        bot.send_message(message.chat.id,
                                         f"<b>{counter}</b>. <a href=\"https://everest.link/project/{project['id']}\">{project['name']}</a>\nAdded: {time:%d.%m.%y %H:%M}\nOwner ID: <b>{project['owner']['id']}</b>\nOwner name: <b>{owner_name}</b>",
                                         reply_markup=default_markup, parse_mode='HTML',
                                         disable_web_page_preview=True)

                    counter += 1
            else:
                bot.send_message(message.chat.id, f"⚠ No projects found on request",
                                    reply_markup=default_markup, parse_mode='HTML')
        except:
            bot.send_message(message.chat.id, f"⚠ Server problem",
                             reply_markup=default_markup, parse_mode='HTML')


    if message.text == "New projects 🔥":
        count = len(get_new_projects(now))

        if count > 0:
            bot.send_message(message.chat.id, f"ℹ Found <b>{count}</b> projects",
                             reply_markup=None, parse_mode='HTML')
            back_markup = types.ForceReply(selective=True)
            bot.send_message(message.chat.id, f"How many recent projects to show?",
                             reply_markup=back_markup)

    try:

        if message.reply_to_message.text:
            text = message.reply_to_message.text

            if text == 'Input project name:':
                bot.send_message(message.chat.id, f"🔍 Project search <b>{message.text}</b>",
                                 reply_markup=default_markup, parse_mode='HTML')

                search = message.text
                data = projects()

                try:

                    data = data['data']['projects']

                    result = []

                    for elem in data:
                        if elem['name'].lower().find(search.lower(), 0) != -1:
                            result.append(elem)

                    count = len(result)

                    if count > 0:
                        bot.send_message(message.chat.id, f"ℹ Found <b>{count}</b> projects",
                                         reply_markup=default_markup, parse_mode='HTML')
                        counter = 1
                        for project in result:
                            time = datetime.datetime.fromtimestamp(float(project['createdAt']))

                            if (project['currentChallenge'] != None):
                                challenged = 'Yes'
                            else:
                                challenged = 'No'
                            owner_name = get_profile(project['owner']['id'])

                            if owner_name == "Unknown":
                                bot.send_message(message.chat.id,
                                                 f"<b>{counter}</b>. <a href=\"https://everest.link/project/{project['id']}\">{project['name']}</a>\nAdded: {time:%d.%m.%y %H:%M}\nChallenged: <b>{challenged}</b>\nOwner ID: <b>{project['owner']['id']}</b>",
                                                 reply_markup=default_markup, parse_mode='HTML',
                                                 disable_web_page_preview=True)
                            else:
                                bot.send_message(message.chat.id,
                                                 f"<b>{counter}</b>. <a href=\"https://everest.link/project/{project['id']}\">{project['name']}</a>\nAdded: {time:%d.%m.%y %H:%M}\nChallenged: <b>{challenged}</b>\nOwner ID: <b>{project['owner']['id']}</b>\nOwner name: <b>{owner_name}</b>",
                                                 reply_markup=default_markup, parse_mode='HTML',
                                                 disable_web_page_preview=True)
                            counter += 1
                    else:
                        bot.send_message(message.chat.id, f"⚠ No projects found on request",
                                         reply_markup=default_markup, parse_mode='HTML')

                except:
                    bot.send_message(message.chat.id, "⚠ Failed to get list of projects",
                                     reply_markup=default_markup,
                                     parse_mode='HTML')


            elif text == 'Input owner ID:':
                bot.send_message(message.chat.id, "Search by owner ID...", reply_markup=default_markup)
                search = message.text.lower()
                try:
                    data = user_projects(f'\"{search}\"')
                    data = data['data']['projects']
                    result = []

                    for elem in data:
                        result.append(elem)
                    count = len(result)
                    if count > 0:
                        bot.send_message(message.chat.id, f"ℹ Found <b>{count}</b> projects",
                                         reply_markup=default_markup, parse_mode='HTML')
                        counter = 1
                        for project in result:
                            time = datetime.datetime.fromtimestamp(float(project['createdAt']))
                            if (project['currentChallenge'] is None):
                                challenged = 'No'
                            else:
                                challenged = 'Yes'
                            bot.send_message(message.chat.id,
                                             f"<b>{counter}</b>. <a href=\"https://everest.link/project/{project['id']}\">{project['name']}</a>\nAdded: {time:%d.%m.%y %H:%M}\nChallenged: <b>{challenged}</b>", reply_markup=default_markup, parse_mode='HTML',
                                                disable_web_page_preview=True)

                            counter += 1
                    else:
                        bot.send_message(message.chat.id, "⚠ No projects found on request",
                                         reply_markup=default_markup, parse_mode='HTML')
                except:
                    bot.send_message(message.chat.id, "⚠ Failed to get list of projects",
                                     reply_markup=default_markup, parse_mode='HTML')
            elif text == 'Input ID for search:':
                bot.send_message(message.chat.id, "Search by user ID...", reply_markup=default_markup)
                search = message.text.lower()
                try:
                    data = user_chellange(f'\"{search}\"')
                    data = data['data']['projects']
                    result=[]
                    for elem in data:
                        for votes in elem['votes']:
                            result.append(votes)
                    count = len(result)
                    if count > 0:
                        bot.send_message(message.chat.id, f"ℹ Found <b>{count}</b> votes",
                                         reply_markup=default_markup, parse_mode='HTML')
                        counter = 1
                        for vote in result:
                            if vote['challenge']['project'] is None:
                                bot.send_message(message.chat.id, f"<b>{counter}</b>. <code>Voting in</code>\nProject: <b>Removed</b>\nChallenge description: {vote['challenge']['description']}\nResolved:<b>{'Yes' if vote['challenge']['resolved'] else 'No'}</b>\nOwner choice:<b>{'Removed' if vote['choice']=='Yes' else 'Keep'}</b>\n",parse_mode='HTML',reply_markup=default_markup,disable_web_page_preview=True)
                            else:
                                bot.send_message(message.chat.id, f"<b>{counter}</b>. <code>Voting in</code>\n Project: <a href=\"https://everest.link/project/{vote['challenge']['project']['id']}\">{vote['challenge']['project']['name']}</a>\nChallenge description: {vote['challenge']['description']}\nResolved: <b>{'Yes' if vote['challenge']['resolved'] else 'No'}</b>\nOwner choice:<b>{'Removed' if vote['choice']=='Yes' else 'Keep'}</b>",reply_markup=default_markup, parse_mode='HTML',disable_web_page_preview=True)
                            counter = counter+1
                    else:
                        bot.send_message(message.chat.id, "⚠ No projects found on request", reply_markup=default_markup, parse_mode='HTML')
                except:
                    bot.send_message(message.chat.id, "⚠ Failed to get list of projects",
                                     reply_markup=default_markup, parse_mode='HTML')



            elif text == f"How many recent projects to show?":
                news = get_new_projects(now)
                answer = message.text
                counter = 1
                if answer.isnumeric():
                    answer = int(answer)
                else:
                    bot.send_message(message.chat.id, "You input incorrect data",
                                     reply_markup=default_markup,
                                     parse_mode='HTML')
                if answer <= len(news) and answer > 0:
                    if len(news) > 0:
                        for project in news:

                            time = datetime.datetime.fromtimestamp(float(project['createdAt']))
                            if (project['currentChallenge'] != None):
                                challenged = 'Yes'
                            else:
                                challenged = 'No'
                            owner_name = get_profile(project['owner']['id'])
                            if owner_name == "Unknown":
                                bot.send_message(message.chat.id,
                                                 f"<b>{counter}</b>. <a href=\"https://everest.link/project/{project['id']}\">{project['name']}</a>\nAdded: {time:%d.%m.%y %H:%M}\nChallenged: <b>{challenged}</b>\nOwner ID: <b>{project['owner']['id']}</b>",
                                                 reply_markup=default_markup, parse_mode='HTML',
                                                 disable_web_page_preview=True)
                            else:
                                bot.send_message(message.chat.id,
                                                 f"<b>{counter}</b>. <a href=\"https://everest.link/project/{project['id']}\">{project['name']}</a>\nAdded: {time:%d.%m.%y %H:%M}\nChallenged: <b>{challenged}</b>\nOwner ID: <b>{project['owner']['id']}</b>\nOwner name: <b>{owner_name}</b>",
                                                 reply_markup=default_markup, parse_mode='HTML',
                                                 disable_web_page_preview=True)
                            if counter == answer:
                                break
                            counter += 1
                else:
                    bot.send_message(message.chat.id, "You input incorrect data",
                                     reply_markup=default_markup,
                                     parse_mode='HTML')

    except:
        pass


if __name__ == '__main__':
    bot.polling()
