# S3 Direct Write (No Local Storage)

Write trading reports, cache, and activity logs directly to S3. Perfect for ephemeral GPU instances.

## What Gets Stored in S3

| Item | Location | When |
|------|----------|------|
| **Reports** | `s3://bucket/reports/daily/YYYY-MM-DD/TICKER/` | After each stock analysis |
| **Cache** | `s3://bucket/cache/fundamentals_cache.json` | After updating cache |
| **Activity DB** | `s3://bucket/cache/activity.db` | After batch completes |

## Setup

### 1. Install boto3
```bash
pip install boto3
# Already in pyproject.toml, so `pip install .` or `uv sync` handles it
```

### 2. Configure AWS Credentials

Either run:
```bash
aws configure
```

Or set directly:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### 3. Set Environment Variables

```bash
export TRADINGAGENTS_S3_BUCKET=lxlomjkanz
export TRADINGAGENTS_S3_ENDPOINT=https://s3api-us-il-1.runpod.io
export TRADINGAGENTS_S3_REGION=us-il-1
```

**Or in `.env` file:**
```ini
TRADINGAGENTS_S3_BUCKET=lxlomjkanz
TRADINGAGENTS_S3_ENDPOINT=https://s3api-us-il-1.runpod.io
TRADINGAGENTS_S3_REGION=us-il-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

## Usage

### Run Batch (Auto-uploads to S3)
```bash
tradingagents batch
```

Everything happens automatically:
1. ✓ Reports uploaded to S3 after each stock
2. ✓ Cache saved to S3 after updates
3. ✓ Activity.db uploaded to S3 at the end

**Result:** No reports stored locally, all in S3.

### Manual Sync (Activity DB only)
```bash
# Upload activity.db to S3
tradingagents sync
```

## How It Works

### Reports (Auto-uploaded)
After analyzing each stock:
```
Stock analysis → Save locally (temp)
              → Upload to S3
              → Clean local copy (optional)
```

**S3 location:** `s3://lxlomjkanz/reports/daily/2026-05-07/AAPL/`
- `complete_report.md` (consolidated)
- `1_analysts/` (market, social, news, fundamentals)
- `2_research/` (bull/bear researcher)
- `3_trading/` (trader proposal)
- `4_risk/` (risk debates)
- `5_portfolio/` (portfolio manager decision)

### Cache (Auto-synced)
Every time a stock's fundamentals status updates:
```
Update cache → Save to S3
```

**S3 location:** `s3://lxlomjkanz/cache/fundamentals_cache.json`

### Activity DB (Uploaded at end)
Local SQLite database used during batch:
```
Batch runs → Activity logged locally (fast)
          → At batch end: Upload to S3
```

**S3 location:** `s3://lxlomjkanz/cache/activity.db`

## Verify It Works

Check S3 bucket:
```bash
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/
```

List today's reports:
```bash
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/reports/daily/2026-05-07/ --recursive
```

Download a report:
```bash
aws s3 cp --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io \
  s3://lxlomjkanz/reports/daily/2026-05-07/AAPL/complete_report.md ./
```

## What Stays Local

Only during analysis:
- **Temporary report files** (cleaned after upload)
- **activity.db** (SQLite, kept for fast I/O, uploaded at end)
- **daily_preset.json** (configuration, doesn't change)

Everything else → S3

## Benefits for GPU Instances

✓ **No disk bloat** — Reports go straight to S3
✓ **No cleanup needed** — Everything uploaded automatically
✓ **Fast I/O** — Local SQLite for activity logging, S3 for final backup
✓ **Crash-safe** — Data persisted to S3 even if instance terminates
✓ **Cost-effective** — No need to manage local storage between runs

## Troubleshooting

### Error: "The specified bucket does not exist"
```
Solution: Check TRADINGAGENTS_S3_BUCKET matches your RunPod bucket
```

### Error: "Unable to locate credentials"
```
Solution: Run `aws configure` or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

### Error: "InvalidEndpointException"
```
Solution: Verify TRADINGAGENTS_S3_ENDPOINT is correct for your RunPod region
```

### Reports not in S3
```
Check: 1) Environment variables are set
       2) AWS credentials are valid
       3) Batch completed without errors
       4) Run `tradingagents sync` to manually upload activity.db
```

### Slow uploads
- Normal for large reports on first upload
- Check internet connection
- Verify boto3 installed: `pip list | grep boto3`

## Environment Variables Reference

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `TRADINGAGENTS_S3_BUCKET` | Yes | `lxlomjkanz` | S3 bucket name |
| `TRADINGAGENTS_S3_ENDPOINT` | No | `https://s3api-us-il-1.runpod.io` | Custom endpoint (RunPod) |
| `TRADINGAGENTS_S3_REGION` | No | `us-il-1` | AWS region (defaults to us-east-1) |
| `AWS_ACCESS_KEY_ID` | Yes | (from aws configure) | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | Yes | (from aws configure) | AWS credentials |

## Advanced: Resume from S3

Download activity.db from previous run:
```bash
aws s3 cp --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io \
  s3://lxlomjkanz/cache/activity.db ~/.tradingagents/activity.db
```

Resume batch:
```bash
tradingagents batch --checkpoint
```

## Performance Notes

- **First batch:** 2-5 min (setup + analysis + S3 uploads)
- **Subsequent batches:** Same (reports uploaded immediately)
- **S3 upload time:** 10-30 sec per stock (depends on report size)
- **Database upload:** 5-10 sec (activity.db at batch end)
- **Bandwidth:** ~5-10 MB per batch (reports + database)

## Next Steps

1. Set environment variables (see Setup)
2. Run `tradingagents batch --setup-only`
3. Edit `~/.tradingagents/daily_preset.json`
4. Run `tradingagents batch`
5. Check S3 bucket for uploaded reports

Done! No local storage needed.
