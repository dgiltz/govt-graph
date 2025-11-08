import os
import json
from pathlib import Path
import praw
import click


@click.group()
def reddit():
    """CLI utilities for Reddit API"""


@reddit.command()
@click.option("--username", required=True, help="Reddit username")
@click.option("--password", required=True, help="Reddit password")
@click.option("--subreddit", required=True, help="Subreddit name (without r/)")
@click.option("--limit", type=int, default=100, help="Number of submissions to download")
@click.option("--output-dir", type=click.Path(), default="./data/reddit", help="Output directory path")
@click.option("--sort", type=click.Choice(["hot", "new", "top", "controversial"]), default="hot", help="Sorting method")
def download_submissions(username: str, password: str, subreddit: str, limit: int, output_dir: str, sort: str):
    """Download submissions from a subreddit to individual JSON files"""

    # Initialize Reddit client
    reddit_client = praw.Reddit(
        client_id=os.environ.get("REDDIT_OAUTH_CLIENT_ID"),
        client_secret=os.environ.get("REDDIT_OAUTH_CLIENT_SECRET"),
        user_agent=f"GovtGraphBot/0.1 by /u/{username}",
        username=username,
        password=password,
    )

    click.echo(f"Authenticated as: {reddit_client.user.me()}")

    # Create output directory structure
    output_path = Path(output_dir) / subreddit / "submissions"
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"Downloading {limit} {sort} submissions from r/{subreddit}...")

    # Get submissions based on sort method
    subreddit_obj = reddit_client.subreddit(subreddit)
    if sort == "hot":
        submissions = subreddit_obj.hot(limit=limit)
    elif sort == "new":
        submissions = subreddit_obj.new(limit=limit)
    elif sort == "top":
        submissions = subreddit_obj.top(limit=limit)
    elif sort == "controversial":
        submissions = subreddit_obj.controversial(limit=limit)

    downloaded = 0
    skipped = 0

    for submission in submissions:
        file_path = output_path / f"{submission.id}.json"

        # Skip if already downloaded
        if file_path.exists():
            skipped += 1
            continue

        # Flatten submission data for relational DB storage
        submission_data = {
            "id": submission.id,
            "title": submission.title,
            "author": str(submission.author) if submission.author else "[deleted]",
            "created_utc": int(submission.created_utc),
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "url": submission.url,
            "selftext": submission.selftext,
            "subreddit": submission.subreddit.display_name,
            "permalink": submission.permalink,
            "is_self": submission.is_self,
            "link_flair_text": submission.link_flair_text,
            "over_18": submission.over_18,
            "spoiler": submission.spoiler,
            "stickied": submission.stickied,
            "locked": submission.locked,
            "distinguished": submission.distinguished,
            "edited": submission.edited if submission.edited else False,
        }

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(submission_data, f, ensure_ascii=False, indent=2)

        downloaded += 1
        if downloaded % 10 == 0:
            click.echo(f"Downloaded {downloaded} submissions...")

    click.echo(f"✓ Downloaded {downloaded} submissions, skipped {skipped} existing files")
    click.echo(f"Output: {output_path}")


@reddit.command()
@click.option("--username", required=True, help="Reddit username")
@click.option("--password", required=True, help="Reddit password")
@click.option("--submission-id", help="Specific submission ID to download comments from")
@click.option("--from-dir", type=click.Path(exists=True), help="Directory containing submission JSON files")
@click.option("--output-dir", type=click.Path(), default="./data/reddit", help="Output directory path")
def download_comments(username: str, password: str, submission_id: str, from_dir: str, output_dir: str):
    """Download comments for submissions to individual JSON files"""

    if not submission_id and not from_dir:
        click.echo("Error: Must specify either --submission-id or --from-dir")
        return

    # Initialize Reddit client
    reddit_client = praw.Reddit(
        client_id=os.environ.get("REDDIT_OAUTH_CLIENT_ID"),
        client_secret=os.environ.get("REDDIT_OAUTH_CLIENT_SECRET"),
        user_agent=f"GovtGraphBot/0.1 by /u/{username}",
        username=username,
        password=password,
    )

    click.echo(f"Authenticated as: {reddit_client.user.me()}")

    # Collect submission IDs
    submission_ids = []
    if submission_id:
        submission_ids = [submission_id]
    else:
        # Read all submission JSON files from directory
        from_path = Path(from_dir)
        for json_file in from_path.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                submission_ids.append(data["id"])

    click.echo(f"Processing {len(submission_ids)} submission(s)...")

    total_downloaded = 0
    total_skipped = 0

    for sub_id in submission_ids:
        submission = reddit_client.submission(id=sub_id)
        subreddit_name = submission.subreddit.display_name

        # Create output directory
        output_path = Path(output_dir) / subreddit_name / "comments"
        output_path.mkdir(parents=True, exist_ok=True)

        # Expand all comments (replace MoreComments objects)
        submission.comments.replace_more(limit=None)

        # Flatten comment tree
        comment_queue = []
        for top_level_comment in submission.comments:
            comment_queue.append((top_level_comment, 0))  # (comment, depth)

        downloaded = 0
        skipped = 0

        while comment_queue:
            comment, depth = comment_queue.pop(0)

            file_path = output_path / f"{comment.id}.json"

            # Skip if already downloaded
            if file_path.exists():
                skipped += 1
                continue

            # Flatten comment data for relational DB storage
            comment_data = {
                "id": comment.id,
                "submission_id": submission.id,
                "parent_id": comment.parent_id,
                "author": str(comment.author) if comment.author else "[deleted]",
                "body": comment.body,
                "created_utc": int(comment.created_utc),
                "score": comment.score,
                "depth": depth,
                "permalink": comment.permalink,
                "is_submitter": comment.is_submitter,
                "distinguished": comment.distinguished,
                "edited": comment.edited if comment.edited else False,
                "stickied": comment.stickied,
            }

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(comment_data, f, ensure_ascii=False, indent=2)

            downloaded += 1

            # Add child comments to queue
            for reply in comment.replies:
                comment_queue.append((reply, depth + 1))

        total_downloaded += downloaded
        total_skipped += skipped
        click.echo(f"  {sub_id}: Downloaded {downloaded} comments, skipped {skipped}")

    click.echo(f"✓ Total: Downloaded {total_downloaded} comments, skipped {total_skipped} existing files")
