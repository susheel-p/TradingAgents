# S3 Sync to RunPod Guide

Copy your trading signals and reports to RunPod S3 storage automatically or manually.

## Setup (One-time)

### 1. Install AWS CLI
```bash
# macOS
brew install awscli

# Windows
choco install awscliv2
# or download: https://aws.amazon.com/cli/

# Linux
apt-get install awscli
```

### 2. Configure AWS CLI Credentials
```bash
aws configure
```

When prompted:
- **AWS Access Key ID**: Your RunPod S3 access key
- **AWS Secret Access Key**: Your RunPod S3 secret key
- **Default region**: `us-il-1` (or your RunPod region)
- **Default output**: `json`

Or directly set in `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

### 3. Set Environment Variables

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.env`):

```bash
# RunPod S3 Bucket (required)
export TRADINGAGENTS_S3_BUCKET=lxlomjkanz

# RunPod S3 Endpoint URL (required for non-AWS providers)
export TRADINGAGENTS_S3_ENDPOINT=https://s3api-us-il-1.runpod.io

# AWS Region (optional, defaults to us-east-1)
export TRADINGAGENTS_S3_REGION=us-il-1
```

**Windows (PowerShell):**
```powershell
$env:TRADINGAGENTS_S3_BUCKET = "lxlomjkanz"
$env:TRADINGAGENTS_S3_ENDPOINT = "https://s3api-us-il-1.runpod.io"
$env:TRADINGAGENTS_S3_REGION = "us-il-1"
```

Or create a `.env` file in your project:
```ini
TRADINGAGENTS_S3_BUCKET=lxlomjkanz
TRADINGAGENTS_S3_ENDPOINT=https://s3api-us-il-1.runpod.io
TRADINGAGENTS_S3_REGION=us-il-1
```

## Usage

### Automatic Sync (on batch exit)
```bash
tradingagents batch
```

When `TRADINGAGENTS_S3_BUCKET` is set, reports automatically sync to S3 when:
- Batch analysis completes
- Process receives SIGTERM or SIGINT (crash detection)
- Program exits normally

Reports sync to: `s3://lxlomjkanz/reports/daily/YYYY-MM-DD/TICKER/`

### Manual Sync (on-demand)

Sync all reports:
```bash
tradingagents sync
```

Sync specific date:
```bash
tradingagents sync --date 2026-05-07
```

### Verify Upload

Check what's in your S3 bucket:
```bash
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/reports/
```

List a specific date:
```bash
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/reports/daily/2026-05-07/
```

Download a report:
```bash
aws s3 cp --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/reports/daily/2026-05-07/AAPL/complete_report.md ./
```

## What Gets Synced

### Automatic Sync (on batch run)
1. **Reports** — All daily analysis results
   - `complete_report.md` (consolidated report)
   - `1_analysts/` — individual analyst reports
   - `2_research/` — research team debate
   - `3_trading/` — trader proposal
   - `4_risk/` — risk management debate
   - `5_portfolio/` — portfolio manager decision

2. **Metadata**
   - `fundamentals_cache.json` — tracks fundamentals update schedule
   - `activity.db` — run history and statistics

### Manual Sync
```bash
tradingagents sync              # All reports
tradingagents sync --date 2026-05-07  # Specific date
```

## Example Workflow

### Day 1: Setup
```bash
# Set environment variables
export TRADINGAGENTS_S3_BUCKET=lxlomjkanz
export TRADINGAGENTS_S3_ENDPOINT=https://s3api-us-il-1.runpod.io
export TRADINGAGENTS_S3_REGION=us-il-1

# Configure AWS CLI
aws configure

# Test connection
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/
```

### Daily: Run Analysis
```bash
# Run batch (reports auto-sync on exit)
tradingagents batch

# Or manually sync if needed
tradingagents sync --date $(date +%Y-%m-%d)
```

### Weekly: Check S3
```bash
# List all reports from this week
aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/reports/daily/ --recursive
```

## Troubleshooting

### Error: "Unable to locate credentials"
```
Solution: Configure AWS CLI credentials with `aws configure`
```

### Error: "The specified bucket does not exist"
```
Solution: Check TRADINGAGENTS_S3_BUCKET matches your RunPod bucket name
```

### Error: "An error occurred (InvalidEndpointException)"
```
Solution: Verify TRADINGAGENTS_S3_ENDPOINT is correct for your RunPod region
```

### Slow Sync
- For large reports, first sync may take minutes
- Check internet connection and RunPod API status
- Monitor with: `aws s3 sync --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/reports --dryrun`

### Verify Files Exist Locally
```bash
# Check local reports directory
ls -la ~/.tradingagents/logs/daily/2026-05-07/AAPL/

# Should show: complete_report.md and subdirectories (1_analysts, 2_research, etc.)
```

## Advanced: Sync Only New Files

Instead of full sync, upload just today's reports:
```bash
DATE=$(date +%Y-%m-%d)
aws s3 sync --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io \
  ~/.tradingagents/logs/daily/$DATE \
  s3://lxlomjkanz/reports/daily/$DATE
```

## Performance Notes

- **Initial setup**: 2-5 minutes (one-time AWS CLI configuration)
- **Daily sync**: 10-30 seconds (depends on report size and internet)
- **Weekly sync**: 1-2 minutes (all reports for that week)
- **Automatic sync on exit**: Happens in background, doesn't block main process

## Security

- AWS credentials are stored locally in `~/.aws/credentials`
- Environment variables are not logged or displayed
- RunPod S3 endpoint is HTTPS only
- Consider using IAM keys with minimal S3 permissions

## Next Steps

1. Set environment variables (see Setup section above)
2. Run `tradingagents batch --setup-only` if you haven't already
3. Run `tradingagents batch` to analyze stocks and auto-sync to S3
4. Check S3: `aws s3 ls --region us-il-1 --endpoint-url https://s3api-us-il-1.runpod.io s3://lxlomjkanz/reports/`
