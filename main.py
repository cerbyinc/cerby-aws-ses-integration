import argparse
import sys

import botocore

from aws import get_current_region, validate_region
from models import HostedZoneRecord, Identity
from repository import (
    AWSHostedZoneRecordsRepository,
    AWSHostedZoneRepository,
    AWSIdentityRepository,
)
from utils import aws_error, confirm, print_banner, prints

parser = argparse.ArgumentParser(
    description="Set AWS SES Service to be integrated with Cerby"
)
parser.add_argument("domain", type=str, help="Domain to configure")
parser.add_argument(
    "--yes", default=False, help="Do not prompt user", action="store_true"
)
args = parser.parse_args()

identity_repo = AWSIdentityRepository()
hz_repo = AWSHostedZoneRepository()
hzr_repo = AWSHostedZoneRecordsRepository()

hosted_zone_id = hz_repo.get(args.domain)
records = hzr_repo.get(hosted_zone_id) if hosted_zone_id else []

collected_records = []


def configure_sending_email(domain: str):
    prints(
        "We are going to configure the AWS SES Identity"
        + f" so you can send emails using {domain}"
    )
    identity = Identity(domain)
    identity = identity_repo.add(identity)
    if identity.verification_status == "Pending":
        identity_records = identity.dkim_tokens_as_records(hosted_zone_id, domain)
        if hosted_zone_id:
            records_to_add = [
                record for record in identity_records if record not in records
            ]
            if confirm(
                "We are going to add the DKIM records to the Hosted Zone,"
                + " do you want to continue?"
            ):
                for record in records_to_add:
                    hzr_repo.add(record)
                    prints(f"DKIM Record {record.name} created")

        else:
            collected_records.extend(identity_records)


def configure_receiving_email(domain: str):
    prints(
        "We are going to configure the AWS SES and your Hosted Zone"
        + f" so you can receive emails using {domain}"
    )
    record = HostedZoneRecord(
        hosted_zone_id,
        domain,
        "MX",
        600,
        [f"10 inbound-smtp.{get_current_region()}.amazonaws.com"],
    )
    if hosted_zone_id:
        if record not in records:
            if confirm(
                "We are going to add the MX record to the Hosted Zone,"
                + " do you want to continue?"
            ):
                hzr_repo.add(record)
                prints(f"DKIM Record {record.name} created")
        else:
            prints("An MX record is already present")
    else:
        collected_records.append(record)


if __name__ == "__main__":
    try:
        print_banner()
        validate_region()
        configure_sending_email(args.domain)
        configure_receiving_email(args.domain)
        sys.exit(0)
    except botocore.exceptions.NoCredentialsError as error:
        aws_error(error)
    except botocore.exceptions.ClientError as error:
        aws_error(error.response["Error"]["Message"])
        sys.exit(1)
    except Exception as error:
        aws_error(error)
    finally:
        if not hosted_zone_id:
            prints(
                "Unable to create records, please add these to your DNS Configuration"
            )
            for record in collected_records:
                print(f"\t- {record.type}, {record.name}, {record.values}")
        print("\nThanks for using Cerby, have a nice day!\n")
