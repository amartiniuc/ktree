"""Main entry point for the ktree application."""

import argparse
import logging
import sys
from pathlib import Path
from ktree.app import KTreeApp


def run() -> None:
    """Run the KTree application."""
    parser = argparse.ArgumentParser(
        description="KTree - Kubernetes Browser CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Kubernetes context to use (default: current context)",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default=None,
        help="Initial namespace to select (default: first namespace)",
    )
    parser.add_argument(
        "--type",
        type=str,
        default=None,
        help="Initial object type to select (e.g., Pods, Services)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to debug.log file",
    )

    args = parser.parse_args()

    # Set up debug logging only if --debug flag is present
    if args.debug:
        DEBUG_LOG_PATH = Path("debug.log")
        if DEBUG_LOG_PATH.exists():
            DEBUG_LOG_PATH.unlink()  # Truncate by deleting and recreating

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(DEBUG_LOG_PATH, mode='w'),  # 'w' mode truncates
            ]
        )
        debug_logger = logging.getLogger('debug')

        # Reduce noise from kubernetes library - set it to INFO level
        logging.getLogger('kubernetes.client').setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        debug_logger.info("=" * 80)
        debug_logger.info("KTree application starting")
        debug_logger.info(f"Arguments: context={args.context}, namespace={args.namespace}, type={args.type}, debug={args.debug}")
    else:
        # When debug is disabled, configure the debug logger to do nothing
        debug_logger = logging.getLogger('debug')
        debug_logger.addHandler(logging.NullHandler())
        debug_logger.propagate = False

    try:
        app = KTreeApp(
            initial_context=args.context,
            initial_namespace=args.namespace,
            initial_type=args.type,
        )
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()

