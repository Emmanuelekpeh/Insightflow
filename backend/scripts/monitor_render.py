#!/usr/bin/env python3
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, TextIO

from backend.services.render_status import RenderStatusMonitor

class StatusLogger:
    def __init__(self, log_file: Optional[TextIO] = None, verbose: bool = False):
        self.log_file = log_file
        self.verbose = verbose

    async def handle_status(self, status_update: dict):
        # Format timestamp
        timestamp = datetime.fromisoformat(status_update['timestamp'])
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Get overall status
        status = status_update['status'].get('status', {}).get('description', 'Unknown')
        
        # Format basic status message
        status_msg = f"\n[{formatted_time}] Overall Status: {status}"
        print(status_msg)

        # Check for incidents
        incidents = status_update.get('incidents', {}).get('incidents', [])
        if incidents:
            print("\nActive Incidents:")
            for incident in incidents:
                incident_msg = f"- {incident['name']}: {incident['status']}"
                print(incident_msg)

        # Check component status if verbose
        if self.verbose:
            components = status_update.get('components', {}).get('components', [])
            if components:
                print("\nComponent Status:")
                for component in components:
                    component_msg = f"- {component['name']}: {component['status']}"
                    print(component_msg)

        # Log to file if specified
        if self.log_file:
            json.dump({
                "timestamp": status_update['timestamp'],
                "status": status_update
            }, self.log_file)
            self.log_file.write('\n')
            self.log_file.flush()

async def main():
    parser = argparse.ArgumentParser(description='Monitor Render.com service status')
    parser.add_argument('--interval', type=int, default=300,
                      help='Check interval in seconds (default: 300)')
    parser.add_argument('--log-file', type=str,
                      help='File to log status updates as JSON')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Show detailed component status')

    args = parser.parse_args()

    # Setup logging
    log_file = None
    if args.log_file:
        log_path = Path(args.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log_path, 'a')

    try:
        logger = StatusLogger(log_file=log_file, verbose=args.verbose)
        monitor = RenderStatusMonitor()
        
        print(f"Starting Render.com status monitor (checking every {args.interval} seconds)")
        print("Press Ctrl+C to stop")
        
        await monitor.monitor(logger.handle_status, interval_seconds=args.interval)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        if log_file:
            log_file.close()
        await monitor.close()

if __name__ == "__main__":
    asyncio.run(main()) 