from time import sleep


def batsignal(
    reddit, what, user, target, report, nap, limit, notifs, if_report_fails_try
):
    report_targets = {}
    print(
        f'batsignal will read {user}\'s history and report anything with "{target}" in it up to {notifs}x per subreddit'
    )

    if what in ["submissions", "both"]:
        print(f"reading {user}'s submission history ...")
        stats = {"failed": 0, "passed": 0}

        for submission in reddit.redditor(user).submissions.new(limit=limit):
            sleep(nap)
            report_submission = False

            if hasattr(submission, "crosspost_parent"):
                print(f"INFO: {submission.permalink} is a crosspost")
                op = reddit.submission(id=submission.crosspost_parent.split("_")[1])
                if (
                    target.lower() in op.title.lower()
                    or target.lower() in op.selftext.lower()
                    or target.lower() in op.url.lower()
                ):
                    report_submission = True
                    print(f"FAIL: crossposted {op.permalink} contains {target} ...")
            if (
                target.lower() in submission.title.lower()
                or target.lower() in submission.selftext.lower()
                or target.lower() in submission.url.lower()
            ):
                report_submission = True
                print(f"FAIL: {submission.permalink} contains {target} ...")

            if report_submission:
                if submission.subreddit in report_targets.keys():
                    if report_targets[submission.subreddit] >= notifs:
                        print(
                            f"      skipping since r/{submission.subreddit} has already received {notifs} reports"
                        )
                        continue
                    report_targets[submission.subreddit] += 1
                else:
                    report_targets[submission.subreddit] = 1

                stats["failed"] += 1
                do_report(submission, report, if_report_fails_try)
            else:
                stats["passed"] += 1
                print(f"PASS: {submission.permalink}")

        print(
            f"done reading {user}'s submission history! pass: {stats['passed']}, fail: {stats['failed']}"
        )

    if what in ["comments", "both"]:
        print(f"reading {user}'s comment history ...")
        stats = {"failed": 0, "passed": 0}

        for comment in reddit.redditor(user).comments.new(limit=limit):
            sleep(nap)
            if target.lower() in comment.body.lower():
                print(f"FAIL: {comment.permalink} contains {target} ...")

                if comment.subreddit in report_targets.keys():
                    if report_targets[comment.subreddit] >= notifs:
                        print(
                            f"      skipping since r/{comment.subreddit} has already received {notifs} reports"
                        )
                        continue
                    report_targets[comment.subreddit] = (
                        report_targets[comment.subreddit] + 1
                    )
                else:
                    report_targets[comment.subreddit] = 1

                stats["failed"] += 1
                do_report(comment, report, if_report_fails_try)

            else:
                stats["passed"] += 1
                print(f"PASS: {comment.permalink}")

        print(
            f"done reading {user}'s comment history! pass: {stats['passed']}, fail: {stats['failed']}"
        )


def do_report(target, report, backup_report):
    try:
        target.report(report)
        print(f"      report complete to r/{target.subreddit}")
        return
    except Exception as e:
        if backup_report == "N/A":
            print(f"      report failed to r/{target.subreddit}, whatever")
            return

    print(f"      custom report failed to r/{target.subreddit}, waiting 200ms ...")
    sleep(0.2)
    try:
        target.report(backup_report)
        print(f"      non-custom report complete to r/{target.subreddit}")
    except Exception as e2:
        print(f"      both reports failed to r/{target.subreddit}, something is wrong")
        pass
