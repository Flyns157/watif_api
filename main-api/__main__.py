import argparse
from . import WatifAPI

def main(debug, host, port):
    WatifAPI().run(debug=debug, host=host, port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Watif API")
    parser.add_argument('--debug', action='store_true', help='Run the API in debug mode')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the API on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the API on')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    if args.verbose:
        print(f"Starting the API on {args.host}:{args.port} with debug={args.debug}")

    main(debug=args.debug, host=args.host, port=args.port)
