import argparse
import praw
from config import *
from time import sleep

parser = argparse.ArgumentParser(
    description=(
        "CLI tool to get known advertisers, spammers, or other unethical marketers reported to all the subreddits they've negatively impacted WITHOUT clogging up subreddit moderation queues."
    )
)
parser.add_argument(
    "-u",
    "--user",
    type=str,
    help="What user is exhibiting bad behavior?",
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

args = parser.parse_args()

reddit = praw.Reddit(
    client_id=praw_client_id,
    client_secret=praw_client_secret,
    refresh_token=praw_refresh_token,
    user_agent="r-cybersecurity/batsignal",
)

report_targets = {}
print(
    f'batsignal will read {args.user}\'s history and report anything with "{args.destroy}" in it up to {args.notifications}x per subreddit'
)

if len(args.override) < 1:
    report_text = f"u/{args.user} is {args.reason} {args.destroy}, check user history"
else:
    report_text = args.override
print(f'reports made will be: "{report_text}", CTRL+C in 5s or batsignal will proceed')
sleep(5)

if args.type in ["submissions", "both"]:
    print(f"reading {args.user}'s submission history ...")
    stats = {"failed": 0, "passed": 0}

    for submission in reddit.redditor(args.user).submissions.new(limit=args.count):
        sleep(args.sleep)
        report_submission = False

        if hasattr(submission, "crosspost_parent"):
            print(f"INFO: {submission.permalink} is a crosspost")
            op = reddit.submission(id=submission.crosspost_parent.split("_")[1])
            if (
                args.destroy.lower() in op.title.lower()
                or args.destroy.lower() in op.selftext.lower()
                or args.destroy.lower() in op.url.lower()
            ):
                report_submission = True
                print(f"FAIL: crossposted {op.permalink} contains {args.destroy} ...")
        if (
            args.destroy.lower() in submission.title.lower()
            or args.destroy.lower() in submission.selftext.lower()
            or args.destroy.lower() in submission.url.lower()
        ):
            report_submission = True
            print(f"FAIL: {submission.permalink} contains {args.destroy} ...")

        if report_submission:
            if submission.subreddit in report_targets.keys():
                if report_targets[submission.subreddit] >= args.notifications:
                    print(
                        f"      skipping since r/{submission.subreddit} has already received {args.notifications} reports"
                    )
                    continue
                report_targets[submission.subreddit] += 1
            else:
                report_targets[submission.subreddit] = 1

            try:
                stats["failed"] += 1
                submission.report(report_text)
                print(f"      report complete to r/{submission.subreddit}")
            except Exception as e:
                print(f"      report failed to r/{submission.subreddit}, whatever")
                pass

        else:
            stats["passed"] += 1
            print(f"PASS: {submission.permalink}")

    print(
        f"done reading {args.user}'s submission history! pass: {stats['passed']}, fail: {stats['failed']}"
    )

if args.type in ["comments", "both"]:
    print(f"reading {args.user}'s comment history ...")
    stats = {"failed": 0, "passed": 0}

    for comment in reddit.redditor(args.user).comments.new(limit=args.count):
        sleep(args.sleep)
        if args.destroy.lower() in comment.body.lower():
            print(f"FAIL: {comment.permalink} contains {args.destroy} ...")

            if comment.subreddit in report_targets.keys():
                if report_targets[comment.subreddit] >= args.notifications:
                    print(
                        f"      skipping since r/{comment.subreddit} has already received {args.notifications} reports"
                    )
                    continue
                report_targets[comment.subreddit] = (
                    report_targets[comment.subreddit] + 1
                )
            else:
                report_targets[comment.subreddit] = 1

            try:
                stats["failed"] += 1
                comment.report(report_text)
                print(f"      report complete to r/{comment.subreddit}")
            except Exception as e:
                print(f"      report failed to r/{comment.subreddit}, whatever")
                pass

        else:
            stats["passed"] += 1
            print(f"PASS: {comment.permalink}")

    print(
        f"done reading {args.user}'s comment history! pass: {stats['passed']}, fail: {stats['failed']}"
    )
