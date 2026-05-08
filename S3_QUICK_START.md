# S3 Direct Write Quick Start

Reports, cache, and activity logs go directly to S3. Perfect for GPU instances.

## 30-Second Setup

```bash
# 1. Configure AWS CLI (one-time)
aws configure
# Enter: Access Key ID, Secret Key, Region (us-il-1), Output (json)

# 2. Set environment variables
export TRADINGAGENTS_S3_BUCKET=lxlomjkanz
export TRADINGAGENTS_S3_ENDPOINT=https://s3api-us-il-1.runpod.io
export TRADINGAGENTS_S3_REGION=us-il-1

# 3. Done! Reports auto-upload to S3
tradingagents batch
```

## Commands

```bash
# Analyze stocks (auto-uploads reports to S3)
tradingagents batch

# Manually upload activity database
tradingagents sync

# Check S3 bucket
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/
```

## What Goes to S3

| Item | Location | When |
|------|----------|------|
| Reports | `s3://lxlomjkanz/reports/daily/YYYY-MM-DD/TICKER/` | After each stock |
| Cache | `s3://lxlomjkanz/cache/fundamentals_cache.json` | After cache update |
| Activity DB | `s3://lxlomjkanz/cache/activity.db` | After batch ends |

## Example: View Report in S3

```bash
# List today's reports
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io \
  s3://lxlomjkanz/reports/daily/2026-05-07/ --recursive

# Download one
aws s3 cp --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io \
  s3://lxlomjkanz/reports/daily/2026-05-07/AAPL/complete_report.md ./
```

## Windows Setup

```powershell
$env:TRADINGAGENTS_S3_BUCKET = "lxlomjkanz"
$env:TRADINGAGENTS_S3_ENDPOINT = "https://s3api-us-il-1.runpod.io"
$env:TRADINGAGENTS_S3_REGION = "us-il-1"
```

Or create `.env` file in project root.

## Local Storage

✓ No reports stored locally (all in S3)
✓ No cache files locally (all in S3)
✓ Activity.db kept local during batch, uploaded at end
✓ Minimal disk usage on GPU instances

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Credentials error | Run `aws configure` |
| Bucket not found | Check `TRADINGAGENTS_S3_BUCKET` matches bucket name |
| Endpoint error | Verify `TRADINGAGENTS_S3_ENDPOINT` URL is correct |

## Full Details

See [S3_DIRECT_WRITE.md](S3_DIRECT_WRITE.md) for complete documentation.
