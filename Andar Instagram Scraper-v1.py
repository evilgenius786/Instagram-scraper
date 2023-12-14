#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from csv import writer
import os.path
import traceback
from datetime import datetime
import os
import instaloader

d = 1
top = 10000
postcount = 7
actioncount = 0
threshold = 5
sindex = 0
pindex = 0
proxies = []


def main():
    """ A client-facing function used to collect information
        needed to scrape Instagram profiles, and to output a
        set of potential partnership prospects.
    """

    # do any initial sestup 
    setup()

    # First, retrieve the accounts the user would like scraped.
    # retrieve_user_accounts()

    # init vars
    global actioncount, L

    # Next, check to see if any accounts exist in Queue.
    # These are accounts we specify, so we want them to run
    # regardless of their qualities, and not get filtered out
    # of Raw Queue.
    num_queue = get_num_accounts_queue()

    # While we're at it, collect the number of accounts in
    # 'Raw Queue' as well.
    num_raw_queue = get_num_accounts_raw_queue()

    # Create account session, if not already logged in
    if loadSessions():

        # create account holder and increase the request
        # count by 1
        L = getIG()

        # actioncount += 1

        # Continue looping until the number of accounts in both
        # Queue and Raw Queue are zero (0).
        while num_queue > 0 or num_raw_queue > 0:

            # if the number of actions sent to a specific account
            # is over the threshold, go ahead and change the
            # account.
            # =============================================================================
            #             if actioncount % threshold == 0:
            #
            #                 # get new account session
            #                 L = getIG()
            # =============================================================================

            # If there are accounts in Queue, process those
            # first. Elif, look at Raw_Queue, else, stop.
            if num_queue > 0:

                # Get first account in Queue file.
                curnt_acct = get_next_account_in_file('Queue.csv')

                # check to see if the account has a depth
                # associated with it by splitting it by a
                # character username can not have.
                if len(curnt_acct.split('-')) > 1:

                    # Does have depth associated with it!
                    # Scrape profile info, and scrape followers
                    # so long as number is greater than 0:
                    if int(curnt_acct[-1]) > 0:

                        # Get account info without any tracer
                        # values.
                        scrape(curnt_acct[:-2])

                        # retrieve the followees from the account
                        followees = [f"{followee}-{int(curnt_acct[-1]) - 1}" for followee in
                                     getFollowees(curnt_acct.split("-")[0])]

                        # add the followees to 'RawQueue.csv'
                        append("RawQueue.csv", followees)

                    else:

                        # Get account info without any tracer
                        # values.
                        scrape(curnt_acct[:-2])

                        # remove the given account from Queue.csv
                        remove_account("Queue.csv", 0)

                    # add the account to scraped and the time
                    # that it was scraped.
                    # append2("Scraped.csv", [f'{curnt_acct}']) # -datetime.now(), '\n'

                else:

                    # Scrape profile information only.
                    scrape(curnt_acct)

                    # Get followees too
                    getFollowees(curnt_acct)

                    followees = [f"{followee}-{d - 1}" for followee in
                                 getFollowees(curnt_acct.split("-")[0])]
                    appendtxt("RawQueue.csv", followees)

                    # After scrape is successful, add data to the
                    # 'prospects' file, remove handle
                    # from Queue.csv, and place handle in
                    # scraped.csv, with corresponding date.
                    remove_account('Queue.csv', 1)

                # Calculate the new amount of accounts in both
                # Queue and Raw Queue to make sure loops stay
                # accurate.
                num_queue = get_num_accounts_queue()
                num_raw_queue = get_num_accounts_raw_queue()

            elif num_raw_queue > 0:

                # Continue iterating in num_raw_queue until there are
                # 500 accounts in Queue, or no more accounts in
                # Raw Queue.
                while num_queue < 500 and num_raw_queue > 0:

                    # Get the first account in Raw Queue
                    curnt_acct = get_next_account_in_file('RawQueue.csv')

                    # With current account, check to see if it
                    # is a valid account that should be scraped.
                    is_valid_acct = is_valid_account(curnt_acct[:-2], curnt_acct)

                    # Is valid account?
                    if is_valid_acct[0]:

                        # Does the account have 10k+ followers?
                        if is_valid_acct[1] == 'Queue':

                            # Acct has 10k+ followers, remove from
                            # Raw Queue and add to Queue
                            append2('Queue.csv',
                                    [f"{curnt_acct[:-2]}-{int(curnt_acct[-1])}"])  # --> May not be correct func.
                            remove_account('RawQueue.csv', 0)  # --> May not be correct func.

                        else:

                            # Acct has >1k followers, remove from Raw
                            # Queue and add to Alt Queue.
                            append2('AltQueue.csv', [f"{curnt_acct[:-2]}-{int(curnt_acct[-1])}"])
                            remove_account('RawQueue.csv', 0)

                    else:

                        # Do not want to scrape this account. Remove
                        # from Raw Queue.
                        remove_account('RawQueue.csv', 0)

                    # Calculate the new amount of accounts in both
                    # Queue and Raw Queue to make sure loops stay
                    # accurate.
                    num_queue = get_num_accounts_queue()
                    num_raw_queue = get_num_accounts_raw_queue()

            else:

                # No accounts exist within Queue or Raw Queue.
                print('Task completed. No further accounts to scrape.')


def getFollowees(user):
    # get global following var
    global L, actioncount

    # accumulator variable for followees
    following = []

    # Loop until you get a a valid account 
    while True:

        try:

            if actioncount % threshold == 0:

                # get a new instagram account session
                getIG()

                # create instagram account holder
                profile = instaloader.Profile.from_username(L.context, user)

            else:

                # create instagram account holder
                profile = instaloader.Profile.from_username(L.context, user)

            break

        except:

            # get a new instagram account session 
            L = getIG()

    # set count to 0 
    count = 0

    # iterate over each of the followers for the given profile
    for follower in profile.get_followees():
        if top == count:
            break
        following.append(follower.username)
        count += 1

    # add one to actioncount
    actioncount += 1

    return following


def retrieve_user_accounts():
    """ Create a CSV file of Instagram account handles by
        asking for user input, converting to a list, and
        iterating over said list.
    """

    # First, have the user enter the handles of the accounts
    # they would like to "start" with. These will go into 
    # Queue.csv to be run regardless of their characteristics. 
    message = 'Please enter each account handle followed by a comma: '

    acct_handles = input(message)

    acct_handles = acct_handles.replace(',', '').split()

    # Check to make sure that the length is greater than
    # zero, or else there are no accounts with which to scrape. 
    # Otherwise, inform the user that they must enter an account. 
    while len(acct_handles) < 1:
        # print error message to user
        print()
        print('Whoops! Please enter at least one account.', end='')

        # request new list from the user
        acct_handles = input(message)

        acct_handles = acct_handles.replace(',', '').split()

    # At this point, we have the profile handles that we need. 
    # We can now write them to the "Queue.csv" file. 
    with open('Queue.csv', 'w', newline='') as file:

        # initialize the writer object
        writer = csv.writer(file)

        # loop over each user-inputted account  
        for acct in acct_handles:
            # add a new line to the CSV file.
            writer.writerow([acct])


def get_num_accounts_queue():
    """ Return the number of rows that exist in Queue.csv """

    # Define accumulator variable to determine num lines.
    num_queue = 0

    # Open Queue file.

    with open('Queue.csv', 'r') as fil:

        queue = fil.read().split('\n')

        if queue == ['']:

            return 0

        else:

            num_queue = len(queue)

            print(f'There are {num_queue:.0f} account(s) in Queue.csv')

            return num_queue


# =============================================================================
#     with open('Queue.csv') as csv_file:
#         # Utilize the built in reader to handle the file
#         csv_reader = csv.reader(csv_file, delimiter=',')
#         queue = []
#         
#         # loop over each row to determine num_rows
# =============================================================================


def get_num_accounts_raw_queue():
    """ Return the number of rows that exist in Raw Queue.csv """

    # Define accumulator variable to determine num lines.
    num_queue = 0

    with open('RawQueue.csv', 'r') as fil:

        rqueue = fil.read().split('\n')

        if rqueue == ['']:

            return 0

        else:

            num_queue = len(rqueue)

            print(f'There are {num_queue:.0f} account(s) in RawQueue.csv')

            return num_queue


# =============================================================================
#     # Open Queue file.
#     with open('RawQueue.csv') as csv_file:
#         # Utilize the built in reader to handle the file
#         csv_reader = csv.reader(csv_file, delimiter=',')
#         rqueue = []
#         # loop over each row to determine num_rows
#         for user in csv_reader:
#             num_queue += 1
#             rqueue.append(user[0])
#         print(f'There are {num_queue:.0f} account(s) in RawQueue.csv')
#         return num_queue
# =============================================================================


def get_next_account_in_file(filename):
    """ Return the first account (corresponding to A1) in
        file (filename), a CSV with a set of instagram
        accounts.
    """
    while True:
        with open(filename, 'r') as fil:
            lines = [line for line in fil.read().split('\n') if line.strip()]
        with open(filename, 'w') as fil:
            fil.write("\n".join(lines))
        return lines[0]


# =============================================================================
#     with open(filename) as csv_file:
#         csv_reader = csv.reader(csv_file, delimiter=',')
#         for line in csv_reader:
#             return line[0]
# =============================================================================


def is_valid_account(account, accountID):
    """ Return a tuple with a bool value indicating whether
        an account (account) meet the criteria to be moved
        from Raw Queue to Queue and whether to put it in
        Queue or Alt Queue.
    """

    # global var
    global L, actioncount

    # First test if the account handle is in Queue, 
    # Alt Queue, or Crawled CSV files. This will keep
    # us from scraping redundantly. 
    # FUTURE FEATURE: SCRAPE IF MORE THAN XX DAYS AFTER
    #                 PREVIOUS SCRAPE.

    while True:

        try:

            if actioncount % threshold == 0:

                # get new instagram session
                getIG()

                # Create profile object of possessed in account.
                profile = instaloader.Profile.from_username(L.context, account)

            else:
                # Create profile object of possessed in account.
                profile = instaloader.Profile.from_username(L.context, account)

            break

        except:

            # if error, get a new instagram session
            L = getIG()

    actioncount = actioncount + 1

    # =============================================================================
    #     # Create profile object of possessed in account.
    #     profile = instaloader.Profile.from_username(L.context, account)
    # =============================================================================

    # BOOLs for determining eligibility of going to Queue
    # or Alt Queue or nowhere. 
    in_scraped = account not in scraped  # I don't update this – will fix. !!!
    is_private = profile.is_private
    followers = profile.followers

    # Has the account been scraped, is it private, and
    # are the followers above 10k? If no, no, yes, add
    # to Queue.csv
    if in_scraped and not is_private and followers > 10000:

        # Print message in console to inform the user
        # what account is being added to Queue and why. 
        print(f"Adding @{account} to Queue.csv because", end='')
        print(" followers > 10,000 and is not private.")

        # Add the account to Queue
        queue.append(account)

        # Write the new list to Queue. 
        # append2('Queue.csv', accountID)
        # writetxt("Queue.csv", queue)

        return [True, 'Queue']

    # Has the account been scraped, is it private, and 
    # are the followers above 1k? If no, no, yes, then 
    # add to AltQueue.csv
    elif in_scraped and not is_private and followers > 1000:

        # Print message in console to inform the user what
        # account is being added to AltQueue and why. 
        print(f"Adding{account} to AltQueue.csv because ", end='')
        print("1,000 < followers < 10,000 and is not private.")

        # Add the account to AltQueue 
        aqueue.append(account)

        # write the account to Alt Queue.
        # append2('AltQueue.csv', accountID)
        # writetxt("AltQueue.csv", aqueue)

        return [True, 'Alt Queue']

    # If neither of these conditions are met, then it is 
    # not worth it to scrape their profile data. 
    else:

        # Print message in the console to inform the user 
        # what account is being skipped and why. 
        # FUTURE :: MAKE THIS MORE ROBUST. 
        print(f"Not adding {account} because is_private =", end='')
        print(f" {is_private} followers = {followers} too low.")

        return [False, "None"]


def remove_account(filename, index):
    """ Remove an account with a given index (index) at
        a certain index (index).
    """

    # Get the lines in the file
    lines = read(filename)

    # Slice so that you get all lines but the first one
    lines = lines[index + 1:]  # does this take all but the first index?

    # Write the file back, with the first line removed. 
    write(filename, lines)


def setup_variables():
    """ Initialize all of the global variables and files
        applicable to running an Instagram Scraper.
    """

    # Define global vars for each of the various files 
    # used throughout the script. 
    global queue, rqueue, aqueue, scraped, prospects

    # Inform the user the depth that newly scraped accounts 
    # will be assigned, and the follower threshold for
    # users to be added to Queue.csv
    print(f"Depth: {d}\t Top followers: {top}")

    # For each of the files, create lists of each of the
    # rows. 

    with open('Queue.csv', 'r') as fil:
        queue = fil.read().split('\n')

    with open('RawQueue.csv', 'r') as fil:
        rqueue = fil.read().split('\n')

    with open('AltQueue.csv', 'r') as fil:
        aqueue = fil.read().split('\n')

    with open('Scraped.csv', 'r') as fil:
        scraped = fil.read().split('\n')

    # =============================================================================
    #     queue = [line[0] for line in read("Queue.csv") if len(read("Queue.csv")) > 0]
    #
    #     rqueue = [line[0] for line in read("RawQueue.csv") if len(read("RawQueue.csv")) > 0]
    #
    #     aqueue = [line[0] for line in read("AltQueue.csv") if len(read("AltQueue.csv")) > 0]
    #
    #     scraped = [line[0] for line in read("Scraped.csv") if len(read("Scraped.csv")) > 0]
    # =============================================================================

    prospects = read("Prospects.csv")


def read(file):
    """ Return a list of rows sourced from a .csv file
        (file).
    """

    # Initialize empty list to act as accumulator for 
    # each row in a given .csv file. 
    lines = []

    # Open the passed file, and get file object. 
    with open(file, mode='r', encoding="utf8") as f:
        # Create a reader object for the given file,
        # for a .csv, use a comma as the separator
        reader = csv.reader(f, delimiter=',')

        # Iterate over each line in the reader object
        for line in reader:
            # For each line, add the data to the
            # lines list. 
            lines.append(line)

    return lines


def write(file, lines):
    """ Add additional data (lines) to a provided
        file (file). Works via appending.
    """

    # Open the specified file and get file object
    with open(file, mode='w+', newline="", encoding="utf8") as f:
        # Create writer object using comma as the
        # chosen separator. 
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        # Write the passed rows by adding them to
        # the end of the file. 
        writer.writerows(lines)


def appendtxt(file, lines):
    """ Write provided date (lines) to the end of
        a provided file.
    """

    # Open the specified file and get file object
    with open(file, mode='a') as f:
        # Using a newline character as the separator
        # add the new data to the end of the file.
        f.write("\n".join(lines))


def writetxt(file, lines):
    """ Write provided date (lines) to the end of
        a provided file.
    """

    # Open the specified file and get file object
    with open(file, mode='w+') as f:
        # Using a newline character as the separator
        # add the new data to the end of the file.
        f.write("\n".join(lines))


def append(file, line):
    """ Open a specified file (file) and append new
        data (lines) to the end of the file.
    """

    # Open the specified file using newline as a blank
    # character and getting the file object. 
    with open(file, mode='a', newline="", encoding="utf8") as f:
        # Create writer object using a comma as the separator.
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        # Write the new data to the end of the file. 
        writer.writerow(line)


# =============================================================================
# def write_to_scraped(file, line):
#     ''' Write to Scraped.csv '''
#     
#     
#     
#     with open(file, mode='a', newline="", encoding="utf8") as f:
#         # Create writer object using a comma as the separator.
#         writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
# 
#         # Write the new data to the end of the file. 
#         writer.writerow(line)
# =============================================================================


def append2(file, line):
    """ Open a specified file (file) and append new
        data (lines) to the end of the file.
    """

    # Open the specified file using newline as a blank
    # character and getting the file object. 

    with open(file, 'a') as f_object:
        # Pass this file object to csv.writer()
        # and get a writer object
        writer_object = writer(f_object)

        # Pass the list as an argument into
        # the writerow()
        writer_object.writerow(line)


def setup():
    """ Ensure all applicable files exist, adn if not,
        create them.
    """

    # Does the folder "sessions" exist? If not. 
    # create the folder. 
    if not os.path.isdir('sessions'):
        # Folder does not exist. Create.
        os.mkdir('sessions')

    # Does the folder "following" exist? If not, 
    # create the folder.
    if not os.path.isdir('following'):
        # Folder does not exist. Create.
        os.mkdir('following')

    # Does the folder "json" exists? If not,
    # create the folder. 
    if not os.path.isdir('json'):
        # Folder does not exist.  Create.
        os.mkdir('json')

    # Does the file "Queue.csv" exist? If not, 
    # create the file. 
    if not os.path.isfile('Queue.csv'):
        # Does not. Create blank file.
        open('Queue.csv', 'a').close()
    # Does the file "Queue.csv" exist? If not,
    # create the file.
    if not os.path.isfile('Proxies.csv'):
        # Does not. Create blank file.
        open('Proxies.csv', 'a').close()
    # Does the file "AltQueue.csv" exist? If not, 
    # create the file. 
    if not os.path.isfile('AltQueue.csv'):
        # Does not. Create blank file.
        open('AltQueue.csv', 'a').close()

    # Does the file "RawQueue.csv" exist? If not,
    # create the file. 
    if not os.path.isfile('RawQueue.csv'):
        # Does not. Create a blank file.
        open('RawQueue.csv', 'a').close()

    # Does the file "Scraped.csv" exist? If not, 
    # create the file. 
    if not os.path.isfile('Scraped.csv'):
        # Does not. Create a blank file.
        open('Scraped.csv', 'a').close()

    # Does the file "UserLogins.csv" exist? If not, 
    # create the file. 
    if not os.path.isfile('UserLogins.csv'):
        # Does not. Create the file with headers.
        write('UserLogins.csv', ['Username', 'Password'])

    # Does the file "Prospects.csv" exist? If not, 
    # create the file. 
    if not os.path.isfile('Prospects.csv'):
        # Does not. Create the file with headers.
        write("Prospects.csv", [
            ['Account Name', 'Name', 'Bio', 'Post Count', 'Follower Count',
             'Following Count', 'Stories', '', 'Post 0', '', '', '', 'Post 1',
             '', '', '', 'Post 2', '', '', '', 'Post 3', '', '', '', 'Post 4',
             '', '', '', 'Post 5', '', '', '', 'Post 6', '', '', '', 'Post 7',
             '', '', ''],
            ['', '', '', '', '', '', '# of Active Frames', 'Time Posted',
             'Date Posted', 'Description', '# of Likes',
             '# of Comments', 'Date Posted', 'Description', '# of Likes',
             '# of Comments', 'Date Posted', 'Description',
             '# of Likes', '# of Comments', 'Date Posted', 'Description',
             '# of Likes', '# of Comments', 'Date Posted',
             'Description', '# of Likes', '# of Comments', 'Date Posted',
             'Description', '# of Likes', '# of Comments',
             'Date Posted', 'Description', '# of Likes', '# of Comments',
             'Date Posted', 'Description', '# of Likes', '# of Comments']])

    # After we ensure the files are created, make
    # sure we setup all global variables. 
    setup_variables()


def scrape(user):
    # Scraping can be error-prone, this will also allow
    # us to get Exception errors 

    # get global account 
    global L, actioncount

    try:

        # Initialize an empty array for new scraped user.
        prospect = []

        # Inform user which user is currently being scraped.
        print(f"Scraping @{user}")

        # Create a profile object for the passed username
        while True:

            try:

                if actioncount % threshold == 0:

                    # get a new insta account session 
                    getIG()

                    # get a new profile object 
                    profile = instaloader.Profile.from_username(L.context, user)

                else:

                    # get a new profile object 
                    profile = instaloader.Profile.from_username(L.context, user)

                break

            except:

                # get a new instagram session 
                L = getIG()

        # Collect the user profile information, and store
        # in a dictionary. Includes all information required,
        # except for the followers & story information.
        info = {"Username": profile.username,
                "Name": profile.full_name,
                "Bio": profile.biography,
                "Followers": profile.followers,
                "Following": profile.followees,
                "Post Count": profile.mediacount}

        # Add each of the data elements to the prospect
        # list.
        prospect.append(info["Username"])
        prospect.append(info["Name"])
        prospect.append(info["Bio"])
        prospect.append(info["Post Count"])
        prospect.append(info["Followers"])
        prospect.append(info["Following"])

        # Initialize an empty list to contain all stories
        # the passed user currently has posted. 
        s = []

        # Iterate over each of the story objects that
        # are currently posted.
        for story in L.get_stories(userids=[profile.userid]):
            # Get the total number of stories currently posted
            info["Story Count"] = story.itemcount

            # Use list comprehension to retrieve the date
            # of each of the stories. 
            s = [str(item.date_utc) for item in story.get_items()]

        # Add stories to the info dictionary 
        info["Story Frames"] = s

        # Add the number of stories to the prospect list 
        # if there are applicable stories.
        prospect.append(info["Story Count"] if "Story Count" in info.keys() else 0)

        # Add the corresponding dates to the prospect list
        # if there are applicable stories.
        prospect.append(info["Story Frames"] if "Story Frames" in info.keys() else 0)

        # Initialize empty dictionary for the lasts n posts.
        posts = {}

        # Initialize an accumulator to determine how many
        # posts we have gotten; only get last n.
        count = 0

        # iterate over each of the 
        for post in profile.get_posts():

            # Have we scraped enough accounts?
            if count == postcount:
                # Yes, exist this loop
                break

            # Create post dictionary object
            posts[f"Post{count}"] = {
                "Date": str(post.date),
                "Description": post.caption,
                "Likes": post.likes,
                "Comments": post.comments
            }

            # Add each of the elements for the post to 
            # the prospect list. Keeping in mind data
            # types! 
            prospect.append(str(post.date))
            prospect.append(post.caption)
            prospect.append(post.likes)
            prospect.append(post.comments)

            # Add one to the accumulator, indicating
            # we scraped a recent post. 
            count += 1

        # Add the post information to the info dictionary
        info["Posts"] = posts

        # Add user to scraped.
        # scraped.append(user)

        # Add prospect object to prospects list
        prospects.append(prospect)

        # Update the Prospects.csv file to include the last
        # scraped user profile
        append("Prospects.csv", prospect)

        # Update the Scraped.csv file to include the last 
        # scraped user profile.
        append2("Scraped.csv", [f'{user}', f'{datetime.now()}'])

        # Update the Queue.csv file 
        # writetxt("Queue.csv", queue)  # Should delete the scraped user?

    # Catches critical errors, and helps to diagnose the issue. 
    except Exception as e:

        traceback.print_exc()

        print(f"Error scraping @{user}", e)

    # add one to the action count
    actioncount += 1


def getProxy():
    # pindex += 1
    # return proxies[(pindex - 1)%len(proxies)]
    return ""


def getIG():
    """ Try to load session of an Instagram user. """

    # Try due to login prone to error. Help to catch
    # exceptions
    global sindex
    user = sessions[sindex % len(sessions)]
    sindex += 1
    proxy = getProxy()
    if proxy != "":
        os.environ['http_proxy'] = proxy
        os.environ['HTTP_PROXY'] = proxy
        os.environ['https_proxy'] = proxy
        os.environ['HTTPS_PROXY'] = proxy

    try:

        # Define Instagram Loader
        L = instaloader.Instaloader()

        # Load the session from corresponding file 
        L.load_session_from_file(username=user, filename=f"./sessions/{user}")

        return L

    except:

        # Remove the user session, if any. 
        os.remove(user)

        # Try again to load session. 
        getIG()


def loadSessions():
    """ Load user sessions for an Instagram Scraper. """

    # Create global variable for sessions
    global sessions

    # Define where the sessions exist, in folder. 
    sessions = os.listdir("./sessions/")

    # Read the UserLogins.csv file to get login info.
    logins = read("UserLogins.csv")

    # If there are no sessions and no login info, user
    # must define some. 
    if len(sessions) == 0 and len(logins) == 0:
        # Print error, notify to add login info.
        print("Please either specify username,password in", end="")
        print("UserLogins.csv or put any session in ./sessions/")

        return False

    # Iterate over each login session, exception first
    for login in logins:

        # Is the first login in sessions? 
        if login[0] not in sessions:
            # No, create session with login.
            createSession(login[0], login[1])

    # Set path to Sessions folder. 
    sessions = os.listdir("./sessions/")

    #  Are there sessions that exist? 
    if len(sessions) > 0:
        # Yes, return 1.
        return True


def createSession(user, pwd):
    """ Create a logged in User Session to store and
        prevent error-prone login interactions.
    """

    # Set scraping object
    L = instaloader.Instaloader()
    print(f"Creating session for {user}")
    # Login using the user provided 
    L.login(user, pwd)

    # Save session file to the sessions directory. 
    L.save_session_to_file(f"./sessions/{user}")

    # Close the file. 
    L.close()


if __name__ == "__main__":
    print()
    main()
