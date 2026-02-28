"""
Log cleanup utility for AI Question Solver.

This script cleans up old log files and session directories based on retention policies.
Can be run manually or scheduled as a cron job.
"""
import argparse
import sys
from solver_logging_config import cleanup_old_logs, LOG_RETENTION_DAYS


def main():
    """Main entry point for log cleanup."""
    parser = argparse.ArgumentParser(
        description="Clean up old AI Question Solver logs and session data"
    )
    parser.add_argument(
        '--retention-days',
        type=int,
        default=LOG_RETENTION_DAYS,
        help=f'Number of days to retain logs (default: {LOG_RETENTION_DAYS})'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    args = parser.parse_args()
    
    print(f"AI Question Solver Log Cleanup")
    print(f"Retention period: {args.retention_days} days")
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be deleted")
        # TODO: Implement dry run mode
        print("Dry run mode not yet implemented")
        return 0
    
    try:
        cleanup_old_logs(retention_days=args.retention_days)
        print("Log cleanup completed successfully")
        return 0
    except Exception as e:
        print(f"Error during log cleanup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
