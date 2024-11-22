from functools import cached_property

from aws import get_current_region
from models import DkimAttributes, HostedZoneRecord, MailFromDomainAttributes
from repository import (
    AWSHostedZoneRecordsRepository,
    AWSHostedZoneRepository,
    AWSIdentityRepository,
)
from utils import prints


class SESActions:
    def __init__(self, domain: str):
        self.domain = domain
        self.region = get_current_region()
        self.identity_repo = AWSIdentityRepository()
        self.hz_repo = AWSHostedZoneRepository()
        self.hzr_repo = AWSHostedZoneRecordsRepository()
        self.hosted_zone_id = self.hz_repo.get(self.domain)
        self.records_pending_to_create = []

    @cached_property
    def hosted_zone_records(self):
        return (
            self.hzr_repo.get(hosted_zone_id=self.hosted_zone_id)
            if self.hosted_zone_id
            else []
        )

    def configure_sending_email(self):
        prints(
            "We are going to configure the AWS SES Identity"
            + f" so you can send emails using {self.domain}"
        )
        identity = DkimAttributes(self.domain)
        identity = self.identity_repo.add_dkim_attributes(identity)
        if identity.verification_status == "Pending":
            identity_records = identity.dkim_tokens_as_records(self.domain)
            if self.hosted_zone_id:
                records_to_add = [
                    record
                    for record in identity_records
                    if record not in self.hosted_zone_records
                ]
                for record in records_to_add:
                    self.hzr_repo.add(self.hosted_zone_id, record)
                    print(f"DKIM Record {record.name} created")
            else:
                self.records_pending_to_create.extend(identity_records)

    def configure_receiving_email(self):
        prints(
            "We are going to configure the AWS SES and your Hosted Zone"
            + f" so you can receive emails using {self.domain}"
        )
        records = {
            "MX": HostedZoneRecord(
                self.domain,
                "MX",
                600,
                [f"10 inbound-smtp.{self.region}.amazonaws.com"],
            )
        }

        if self.hosted_zone_id:
            for record_type, record in records.items():
                if record not in self.hosted_zone_records:
                    self.hzr_repo.add(self.hosted_zone_id, record)
                    prints(f"{record_type} Record {record.name} created")
                else:
                    prints(f"A {record_type} record is already present")
        else:
            self.records_pending_to_create.extend(records.values())

    def configure_mail_from_domain(self):
        prints(
            f"We are going to configure the MAIL FROM of AWS SES identity {self.domain}"
            f"by default is set to bounce.{self.domain}"
        )
        mail_from_domain = f"bounce.{self.domain}"

        records = {
            "MX": HostedZoneRecord(
                mail_from_domain,
                "MX",
                600,
                [f"10 inbound-smtp.{self.region}.amazonaws.com"],
            ),
            "TXT": HostedZoneRecord(
                mail_from_domain,
                "TXT",
                600,
                ['"v=spf1 include:amazonses.com ~all"'],
            ),
        }

        attributes = MailFromDomainAttributes(
            name=self.domain, mail_from_domain=mail_from_domain
        )
        domain_status = self.identity_repo.add_mail_from_domain_attributes(attributes)

        if domain_status.mail_from_domain_status != "Pending":
            self.records_pending_to_create.extend(records.values())
            return

        if self.hosted_zone_id:
            for record_type, record in records.items():
                if record not in self.hosted_zone_records:
                    self.hzr_repo.add(self.hosted_zone_id, record)
                    prints(f"{record_type} Record {record.name} created")
                else:
                    prints(f"A {record_type} record is already present")
        else:
            self.records_pending_to_create.extend(records.values())
