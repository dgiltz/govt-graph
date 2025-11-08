# civics-graph

## CLI Usage

### Reddit Data Downloader

Download Reddit submissions and comments for analysis.

**Prerequisites:**
- Set environment variables: `REDDIT_OAUTH_CLIENT_ID` and `REDDIT_OAUTH_CLIENT_SECRET`
- Have Reddit account credentials

**Download submissions:**
```bash
pdm run govt-graph reddit download-submissions \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --subreddit politics \
  --limit 100 \
  --sort hot \
  --output-dir ./data/reddit
```

**Download comments:**
```bash
# For all submissions in a directory
pdm run govt-graph reddit download-comments \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --from-dir ./data/reddit/politics/submissions \
  --output-dir ./data/reddit

# For a specific submission
pdm run govt-graph reddit download-comments \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --submission-id abc123 \
  --output-dir ./data/reddit
```

**Output structure:**
```
data/reddit/
  {subreddit}/
    submissions/
      {submission_id}.json
    comments/
      {comment_id}.json
```

Each JSON file contains flattened data ready for relational database import.

## APIs
## [FEC Finance Data](https://api.open.fec.gov/swagger/
## [Library of Congress: Congressional Data](https://www.loc.gov/apis/additional-apis/congress-dot-gov-api/)
## data.gov
### [Congressional Districts](https://catalog.data.gov/dataset/u-s-congressional-districts-91554/resource/23de98b1-b425-4fe1-b76c-af10306ba2d3)
## Election Data
### [Associated Press API](https://developer.ap.org/ap-elections-api/)
### [Google civic info](https://developers.google.com/civic-information)
### [Civic Engine](https://organizations.ballotready.org/ballotready-api)
