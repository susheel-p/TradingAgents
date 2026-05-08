"""S3 storage backend for reports, cache, and activity logs."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception


class S3Storage:
    """Handle reading/writing to S3 for reports, cache, and activity logs."""

    def __init__(self):
        self.bucket = os.getenv("TRADINGAGENTS_S3_BUCKET")
        self.endpoint_url = os.getenv("TRADINGAGENTS_S3_ENDPOINT")
        self.region = os.getenv("TRADINGAGENTS_S3_REGION", "us-east-1")
        self.enabled = bool(self.bucket)
        self._client = None

    @property
    def client(self):
        """Lazy-load S3 client."""
        if not self.enabled:
            return None
        if self._client is None:
            if not boto3:
                raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
            session = boto3.Session(region_name=self.region)
            kwargs = {"region_name": self.region}
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            self._client = session.client("s3", **kwargs)
        return self._client

    def upload_report(self, report_path: Path, ticker: str, analysis_date: str) -> Optional[str]:
        """Upload complete_report.md to S3.

        Args:
            report_path: Local path to complete_report.md
            ticker: Stock ticker
            analysis_date: Analysis date (YYYY-MM-DD)

        Returns:
            S3 key if successful, None if S3 not enabled or error
        """
        if not self.enabled or not report_path.exists():
            return None

        try:
            s3_key = f"reports/daily/{analysis_date}/{ticker}/complete_report.md"
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=content.encode("utf-8"),
                ContentType="text/markdown",
            )
            return f"s3://{self.bucket}/{s3_key}"
        except (ClientError, Exception) as e:
            print(f"Warning: Failed to upload report to S3: {e}")
            return None

    def upload_report_directory(self, local_dir: Path, ticker: str, analysis_date: str) -> Optional[str]:
        """Upload entire report directory to S3.

        Args:
            local_dir: Local directory containing report files (e.g., ~/.tradingagents/logs/daily/2026-05-07/AAPL)
            ticker: Stock ticker
            analysis_date: Analysis date (YYYY-MM-DD)

        Returns:
            S3 prefix if successful, None if S3 not enabled or error
        """
        if not self.enabled or not local_dir.exists():
            return None

        try:
            s3_prefix = f"reports/daily/{analysis_date}/{ticker}"
            for file_path in local_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(local_dir)
                    s3_key = f"{s3_prefix}/{relative_path.as_posix()}"
                    with open(file_path, "rb") as f:
                        self.client.put_object(
                            Bucket=self.bucket,
                            Key=s3_key,
                            Body=f.read(),
                        )
            return f"s3://{self.bucket}/{s3_prefix}"
        except (ClientError, Exception) as e:
            print(f"Warning: Failed to upload report directory to S3: {e}")
            return None

    def load_cache(self) -> Dict[str, str]:
        """Load fundamentals cache from S3.

        Returns:
            Cache dict (ticker -> last_analysis_date)
        """
        if not self.enabled:
            return {}

        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key="cache/fundamentals_cache.json",
            )
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError:
            # File doesn't exist yet
            return {}
        except Exception as e:
            print(f"Warning: Failed to load cache from S3: {e}")
            return {}

    def save_cache(self, cache: Dict[str, str]) -> bool:
        """Save fundamentals cache to S3.

        Args:
            cache: Cache dict (ticker -> last_analysis_date)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return True

        try:
            content = json.dumps(cache, indent=2)
            self.client.put_object(
                Bucket=self.bucket,
                Key="cache/fundamentals_cache.json",
                Body=content.encode("utf-8"),
                ContentType="application/json",
            )
            return True
        except (ClientError, Exception) as e:
            print(f"Warning: Failed to save cache to S3: {e}")
            return False

    def upload_activity_db(self, db_path: Path) -> Optional[str]:
        """Upload activity.db to S3.

        Args:
            db_path: Local path to activity.db

        Returns:
            S3 key if successful, None if S3 not enabled or error
        """
        if not self.enabled or not db_path.exists():
            return None

        try:
            s3_key = "cache/activity.db"
            with open(db_path, "rb") as f:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=f.read(),
                )
            return f"s3://{self.bucket}/{s3_key}"
        except (ClientError, Exception) as e:
            print(f"Warning: Failed to upload activity.db to S3: {e}")
            return None

    def download_activity_db(self, db_path: Path) -> bool:
        """Download activity.db from S3 (optional, for resuming runs).

        Args:
            db_path: Local path where to save activity.db

        Returns:
            True if successful or file doesn't exist, False if error
        """
        if not self.enabled:
            return True

        try:
            self.client.download_file(
                self.bucket,
                "cache/activity.db",
                str(db_path),
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                # File doesn't exist yet (first run)
                return True
            print(f"Warning: Failed to download activity.db from S3: {e}")
            return False
        except Exception as e:
            print(f"Warning: Failed to download activity.db from S3: {e}")
            return False


# Singleton instance
_s3_storage = None


def get_s3_storage() -> S3Storage:
    """Get or create S3 storage instance."""
    global _s3_storage
    if _s3_storage is None:
        _s3_storage = S3Storage()
    return _s3_storage
