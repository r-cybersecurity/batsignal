import argparse
import praw
import os
from time import sleep
from config import *
from batsignal import batsignal

parser = argparse.ArgumentParser(
    description=(
        "CLI tool to get known advertisers, spammers, or other unethical marketers reported to all the subreddits they've negatively impacted WITHOUT clogging up subreddit moderation queues."
    )
)
parser.add_argument(
    "-u",
    "--user",
    type=str,
    help="What user is exhibiting bad behavior? (or: a file containing a list of usernames, one per line)",
    required=True,
)
parser.add_argument(
    "-r",
    "--reason",
    type=str,
    help="What is the specific bad behavior (ex. guerrilla marketing, advertising, spamming)?",
    required=True,
)
parser.add_argument(
    "-x",
    "--destroy",
    type=str,
    help="What string should each post/comment contain to warrant a report?",
    required=True,
)
parser.add_argument(
    "-o",
    "--override",
    type=str,
    help="Specify your own report message, otherwise uses a default composition.",
    default="",
)
parser.add_argument(
    "-t",
    "--type",
    type=str,
    help="Should batsignal check posts, comments, or both?",
    default="both",
    choices={"submissions", "comments", "both"},
)
parser.add_argument(
    "-c",
    "--count",
    type=int,
    help="How many posts/comments should we check? Default: 10k (all)",
    default=10000,
)
parser.add_argument(
    "-n",
    "--notifications",
    type=int,
    help="How many reports should each impacted subreddit receive? Default: 1",
    default=1,
)
parser.add_argument(
    "-s",
    "--sleep",
    type=int,
    help="How many seconds should we sleep between checking each submission/comment? Default: 1",
    default=1,
)
parser.add_argument(
    "-i",
    "--if-report-fails-try",
    type=str,
    help="If custom reports aren't accepted, what should we report the content as? Default: N/A",
    default="N/A",
    choices={"Spam", "N/A"},
)

args = parser.parse_args()

if os.path.isfile(args.user):
    with open(args.user) as f:
        users = [line.rstrip("\n") for line in f]
else:
    users = [args.user]

reddit = praw.Reddit(
    client_id=praw_client_id,
    client_secret=praw_client_secret,
    refresh_token=praw_refresh_token,
    user_agent="r-cybersecurity/batsignal",
)

for user in users:
    if len(args.override) < 1:
        report_text = f"u/{user} is {args.reason} {args.destroy}, check user history"
    else:
        report_text = args.override

    batsignal.batsignal(
        reddit,
        args.type,
        user,
        args.destroy,
        report_text,
        args.sleep,
        args.count,
        args.notifications,
        args.if_report_fails_try,
    )
