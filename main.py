import argparse
import sys

import botocore

from aws import validate_region
from ses_actions import SESActions
from utils import aws_error, print_banner, prints


def get_args():
    parser = argparse.ArgumentParser(
        description="Set AWS SES Service to be integrated with Cerby"
    )
    parser.add_argument(
        "domain", type=str, help="Domain to configure, e.g. cerby.company.com"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        help="Workspace to configure, e.g. your-company from your-company.cerby.com",
        required=False,
    )
    return parser.parse_args()


def main():
    args = get_args()
    collected_records = []
    failed_rules = {}
    try:
        print_banner()
        validate_region()
        ses_actions = SESActions(domain=args.domain)
        ses_actions.configure_sending_email()
        ses_actions.configure_receiving_email()
        ses_actions.configure_mail_from_domain()
        collected_records = ses_actions.records_pending_to_create
        if args.workspace:
            ses_actions.configure_email_receiving_rules(workspace=args.workspace)
            failed_rules = ses_actions.rules_failed_to_create
        sys.exit(0)
    except botocore.exceptions.NoCredentialsError as error:
        aws_error(error)
    except botocore.exceptions.ClientError as error:
        aws_error(error.response["Error"]["Message"])
        sys.exit(1)
    except Exception as error:
        aws_error(str(error))
    finally:
        if collected_records:
            prints(
                "Oops! We were unable to create the records, please add these to your DNS service"
            )
            for record in collected_records:
                print(f"\t- {record.type}, {record.name}, {record.values}")

        if failed_rules:
            prints("Failed to create the following rules:")
            for name, error in failed_rules.items():
                print(f"\t- {name}: {error}")

        print("\nThanks for using Cerby, have a nice day!\n")


if __name__ == "__main__":
    main()
