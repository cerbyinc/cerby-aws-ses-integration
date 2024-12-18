from functools import cached_property

from aws import get_current_region
from exceptions import (
    RuleAlreadyExistsException,
    RuleSetAlreadyExistsException,
    RuleSetDoesNotExistException,
)
from models import (
    DkimAttributes,
    HostedZoneRecord,
    MailFromDomainAttributes,
    ReceiptRule,
)
from repository import (
    AWSHostedZoneRecordsRepository,
    AWSHostedZoneRepository,
    AWSIdentityRepository,
    AWSReceiptRulesRepository,
)
from utils import prints


class SESActions:
    def __init__(self, domain: str):
        self.domain = domain
        self.region = get_current_region()
        self.identity_repo = AWSIdentityRepository()
        self.hz_repo = AWSHostedZoneRepository()
        self.hzr_repo = AWSHostedZoneRecordsRepository()
        self.receipt_rules_repo = AWSReceiptRulesRepository()
        self.hosted_zone_id = self.hz_repo.get(self.domain)
        self.records_pending_to_create = []
        self.rules_failed_to_create = {}

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
                [f"10 feedback-smtp.{self.region}.amazonses.com"],
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

        if domain_status.mail_from_domain_status not in ["Pending", "Success"]:
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

    def configure_email_receiving_rules(self, workspace: str):
        prints("We are going to configure the receving rule set")

        name = f"rule-set-for-cerby-{workspace}"

        try:
            self.receipt_rules_repo.create_receipt_rule_set(rule_set_name=name)
        except RuleSetAlreadyExistsException:
            prints(f"Rule set '{name}' already exists.")
        except Exception as e:
            self.rules_failed_to_create[name] = str(e)
            raise e

        proxy_rule = ReceiptRule(name=name, rule_set_name=name)
        proxy_rule.create_proxy_rule(
            bucket_name="cerby-store-ses-email-production", prefix="staged"
        )

        try:
            self.receipt_rules_repo.create_receipt_rule(rule=proxy_rule)
        except RuleAlreadyExistsException:
            prints(f"Rule '{name}' already exists.")
        except Exception as e:
            self.rules_failed_to_create[name] = str(e)
            raise e

        try:
            self.receipt_rules_repo.set_active_receipt_rule_set(rule_set_name=name)
            prints(f"Rule set '{name}' activated.")
        except RuleSetDoesNotExistException:
            prints(f"Unable to active Rule set '{name}', it does not exist.")
        except Exception as e:
            self.rules_failed_to_create[name] = str(e)
            raise e
