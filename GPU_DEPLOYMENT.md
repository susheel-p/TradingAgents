# GPU Deployment: Safe Batch Analysis with Auto-Sync

For on-demand GPU instances that may crash or terminate unexpectedly, TradingAgents batch automatically syncs critical data to S3.

---

## Quick Start (Optional)

S3 sync is **disabled by default**. To enable, set one environment variable:

### 1. Set Environment Variable (Optional)

```bash
export TRADINGAGENTS_S3_BUCKET="my-bucket"
```

Or in your deployment script (Lambda, ECS, etc.):

```bash
#!/bin/bash
export TRADINGAGENTS_S3_BUCKET="my-bucket-name"  # Optional
python -m cli.main batch stocks_today.txt
```

**If not set:** Batch runs normally without S3 sync.

### 2. Configure AWS Credentials

Ensure AWS CLI can access your bucket:

```bash
# Option A: IAM role (recommended for EC2, Lambda, ECS)
# No explicit credentials needed if instance has S3 access

# Option B: AWS credentials file
aws configure
# or
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### 3. Run Batch

```bash
tradingagents batch stocks_today.txt
```

**That's it!** On exit (normal or crash), these files auto-sync to S3:
- `fundamentals_cache.json` — tells next run which stocks already ran fundamentals
- `activity.db` — dashboard history and run logs

---

## What Gets Synced

| File | Purpose | Auto-Syncs |
|------|---------|-----------|
| `~/.tradingagents/fundamentals_cache.json` | Tracks when fundamentals ran per stock | ✅ Yes |
| `~/.tradingagents/activity.db` | Dashboard history, agent timelines, tokens | ✅ Yes |
| `~/.tradingagents/daily_preset.json` | Configuration | ❌ No (just config) |

---

## How It Works

### 1. On Batch Start
```python
setup_sync_trap()  # Register exit handlers
```

### 2. On Exit (Normal or Crash)
Syncs files to S3 via:
- `SIGTERM` — graceful shutdown
- `SIGINT` — Ctrl+C
- `atexit` — normal exit
- (If crash: OS signals trigger sync before termination)

### 3. On Next Run
Download from S3:
```bash
aws s3 cp s3://my-bucket/fundamentals_cache.json ~/.tradingagents/
aws s3 cp s3://my-bucket/activity.db ~/.tradingagents/
```

---

## Deployment Patterns

### AWS Lambda

```python
import os
os.environ["TRADINGAGENTS_S3_BUCKET"] = "my-bucket"

def lambda_handler(event, context):
    import subprocess
    subprocess.run(["python", "-m", "cli.main", "batch", "stocks_today.txt"])
    return {"statusCode": 200}
```

**Lambda execution role must have S3 access:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
}
```

### AWS ECS Task

```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install .

ENV TRADINGAGENTS_S3_BUCKET="my-bucket"
ENV AWS_DEFAULT_REGION="us-east-1"

CMD ["python", "-m", "cli.main", "batch", "stocks_today.txt"]
```

**Task role must have S3 access** (see Lambda policy above).

### EC2 Instance (with cron)

```bash
#!/bin/bash
# /opt/batch_daily.sh

export TRADINGAGENTS_S3_BUCKET="my-bucket"
export AWS_DEFAULT_REGION="us-east-1"

# Download before (if instance is ephemeral)
aws s3 cp s3://my-bucket/fundamentals_cache.json ~/.tradingagents/ 2>/dev/null || true
aws s3 cp s3://my-bucket/activity.db ~/.tradingagents/ 2>/dev/null || true

# Run batch (auto-syncs on exit)
python -m cli.main batch stocks_today.txt

# Exit code doesn't matter; sync already happened
exit 0
```

Crontab:
```bash
0 9 * * *  /opt/batch_daily.sh >> /var/log/batch.log 2>&1
```

### Google Cloud Run

```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install .

ENV TRADINGAGENTS_S3_BUCKET="gs://my-bucket"
ENV CLOUDSDK_PYTHON=/usr/bin/python3

CMD ["python", "-m", "cli.main", "batch", "stocks_today.txt"]
```

Uses `gs://` bucket syntax (GCS instead of S3).

---

## Monitoring Syncs

### View S3 Bucket

```bash
# List sync'd files
aws s3 ls s3://my-bucket/ --recursive

# Download latest cache
aws s3 cp s3://my-bucket/fundamentals_cache.json .
cat fundamentals_cache.json
```

### Check Logs During Sync

When S3 sync is enabled, batch shows:

```
Batch Analysis Runner

Loading preset configuration...
Loading stocks list...
+ 10 stocks loaded: AAPL, MSFT, ...
+ Analysis date: 2026-05-06
+ LLM Provider: ANTHROPIC
+ Output language: English
+ Fundamentals: Weekly
S3 sync enabled: my-bucket

[1/10] Analyzing AAPL...
...
```

---

## Troubleshooting

### "S3 sync enabled but files don't appear in bucket"

**Possible causes:**
1. AWS credentials not configured
   ```bash
   aws s3 ls s3://my-bucket/  # Test access
   ```

2. Batch completes before sync finishes (very fast runs)
   - Sync timeout is 30 seconds; slower batches should complete in time
   - If batch < 5 seconds, sync may race

3. Instance crashes before sync completes
   - Signal handlers still trigger sync
   - If crash happens immediately, data may be lost
   - Consider retry logic with S3 persistence across runs

### "Files in S3 but batch doesn't download them"

Ensure download script runs before batch:

```bash
aws s3 cp s3://my-bucket/fundamentals_cache.json ~/.tradingagents/ 2>/dev/null || true
python -m cli.main batch stocks_today.txt
```

### "activity.db is too large"

Clean old data:

```bash
# Delete activity data older than 30 days
sqlite3 ~/.tradingagents/activity.db \
  "DELETE FROM runs WHERE started_at < datetime('now', '-30 days');"
aws s3 cp ~/.tradingagents/activity.db s3://my-bucket/
```

---

## Advanced: Custom Sync Strategy

If S3 doesn't fit your deployment, override the sync function:

```python
# In cli/preset.py or your own module
import os

def custom_sync(cache_file, activity_db):
    """Upload to your storage (GCS, Azure Blob, etc.)."""
    import google.cloud.storage
    bucket = google.cloud.storage.Client().bucket('my-bucket')
    bucket.blob('fundamentals_cache.json').upload_from_filename(str(cache_file))
    bucket.blob('activity.db').upload_from_filename(str(activity_db))

def setup_sync_trap(cache_file=None, activity_db=None):
    """Use custom sync instead of S3."""
    import signal
    import atexit
    
    def on_exit(signum=None, frame=None):
        custom_sync(cache_file, activity_db)
    
    signal.signal(signal.SIGTERM, on_exit)
    signal.signal(signal.SIGINT, on_exit)
    atexit.register(on_exit)
```

Then in batch command:

```python
from cli.preset import setup_sync_trap
setup_sync_trap(custom_sync_fn=custom_sync)
```

---

## Cost Impact

**Example: 10 stocks × 5 days/week**

| Scenario | Fundamentals Runs | S3 Cost |
|----------|------------------|---------|
| Daily fundamentals (no cache) | 50/week | $0.05/month |
| Weekly fundamentals (cache) | 10/week | $0.01/month |
| Force check cache | 1 check/week | < $0.01/month |

**S3 pricing (us-east-1):**
- PUT: $0.000005 per request (fundamentals_cache.json + activity.db = 2 requests)
- GET: $0.0000004 per request

**Negligible cost.** Primarily benefits in **avoided GPU compute hours**.

---

## Examples

### Example 1: Daily Batch on AWS Lambda

**Lambda function (Python):**
```python
import os
import subprocess

def lambda_handler(event, context):
    os.environ["TRADINGAGENTS_S3_BUCKET"] = "trading-agents-data"
    result = subprocess.run(
        ["python", "-m", "cli.main", "batch", "stocks_today.txt"],
        capture_output=True,
        text=True
    )
    return {
        "statusCode": 0 if result.returncode == 0 else 1,
        "body": result.stdout + result.stderr
    }
```

**CloudWatch Events rule:**
- Trigger: Daily at 9:00 AM UTC
- Target: Lambda function above

**Flow:**
1. Lambda starts
2. Batch runs, syncs to S3 on exit
3. Next day, Lambda runs again
4. Downloads cache from S3, knows which stocks need fundamentals
5. Avoids redundant fundamentals (saves GPU cost)

### Example 2: Scheduled EC2 Spot Instance

**Launch template:**
```bash
#!/bin/bash
set -e

# Install (if new instance)
cd /home/ubuntu
git clone ... trading-agents
cd trading-agents
pip install .

# Download cache from persistent storage
aws s3 cp s3://my-bucket/fundamentals_cache.json ~/.tradingagents/ || true
aws s3 cp s3://my-bucket/activity.db ~/.tradingagents/ || true

# Batch run (auto-syncs on exit)
export TRADINGAGENTS_S3_BUCKET="my-bucket"
python -m cli.main batch stocks_today.txt

# (Instance terminates or continues on next schedule)
```

---

## Summary

✅ **What you get:**
- Fundamentals cache survives instance crashes
- Dashboard history preserved across runs
- No manual backup/restore needed
- Single environment variable to enable

✅ **What it does:**
- Auto-syncs on: SIGTERM, SIGINT, normal exit
- Robust against crashes and terminations
- Minimal cost (S3 is cheap)
- Works with Lambda, ECS, EC2, any cloud provider

Ready to deploy! Set `TRADINGAGENTS_S3_BUCKET` and run batch.
