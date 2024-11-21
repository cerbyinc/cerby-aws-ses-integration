from typing import List, Optional

from aws import get_client
from models import DkimAttributes, HostedZoneRecord, MailFromDomainAttributes


class AWSIdentityRepository:
    def __init__(self) -> None:
        super().__init__()
        self.client = get_client("ses")

    def add_dkim_attributes(self, new: DkimAttributes) -> DkimAttributes:
        identity = self.get_dkim_attributes(new.name)
        if identity:
            new = identity
        else:
            response = self.client.verify_domain_dkim(Domain=new.name)
            new.dkim_tokens = response["DkimTokens"]
            new.verification_status = "Pending"
        return new

    def get_dkim_attributes(self, name: str) -> Optional[DkimAttributes]:
        identities = self.client.get_identity_dkim_attributes(Identities=[name])
        if name in identities["DkimAttributes"]:
            attributes = identities["DkimAttributes"][name]
            return DkimAttributes(
                name=name,
                dkim_tokens=attributes["DkimTokens"],
                verification_status=attributes["DkimVerificationStatus"],
            )
        else:
            return None

    def add_mail_from_domain_attributes(self, new: MailFromDomainAttributes):
        attributes = self.get_mail_from_domain_attributes(new.name)
        if attributes and new.mail_from_domain:
            new = attributes
        else:
            self.client.set_identity_mail_from_domain(
                Identity=new.name,
                BehaviorOnMXFailure=new.behavior_on_mx_failure,
                MailFromDomain=new.mail_from_domain,
            )
            new.mail_from_domain_status = "Pending"
        return new

    def get_mail_from_domain_attributes(
        self, name: str
    ) -> Optional[MailFromDomainAttributes]:
        identity = self.client.get_identity_mail_from_domain_attributes(
            Identities=[name]
        )
        if name in identity["MailFromDomainAttributes"]:
            attributes = identity["MailFromDomainAttributes"][name]
            if attributes.get("MailFromDomain", None) is None:
                return None
            return MailFromDomainAttributes(
                name=name,
                behavior_on_mx_failure=attributes["BehaviorOnMXFailure"],
                mail_from_domain=attributes["MailFromDomain"],
                mail_from_domain_status=attributes["MailFromDomainStatus"],
            )
        return None


class AWSHostedZoneRepository:
    def __init__(self) -> None:
        super().__init__()
        self.client = get_client("route53")

    def get(self, domain: str) -> Optional[str]:
        hosted_zones = self.client.list_hosted_zones_by_name(DNSName=domain)[
            "HostedZones"
        ]
        hosted_zone = next(
            (
                hosted_zone
                for hosted_zone in hosted_zones
                if domain in hosted_zone["Name"]
            ),
            None,
        )
        if hosted_zone:
            return hosted_zone["Id"]
        return None


class AWSHostedZoneRecordsRepository:
    def __init__(self) -> None:
        super().__init__()
        self.client = get_client("route53")

    def add(self, hosted_zone_id: str, record: HostedZoneRecord):
        values = []
        for value in record.values:
            values.append({"Value": value})

        change = {
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": record.name,
                "Type": record.type,
                "TTL": record.ttl,
                "ResourceRecords": values,
            },
        }

        self.client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "For Cerby AWS SES Integration",
                "Changes": [change],
            },
        )

    def get(self, hosted_zone_id: str) -> List[HostedZoneRecord]:
        response = self.client.list_resource_record_sets(HostedZoneId=hosted_zone_id)
        resource_record_sets = response["ResourceRecordSets"]
        records = []
        for record_set in resource_record_sets:
            values = []
            if record_set.get("Type", "") in ["CNAME", "TXT", "MX"]:
                for resource_record in record_set.get("ResourceRecords", []):
                    values.append(resource_record["Value"])
                records.append(
                    HostedZoneRecord(
                        record_set.get("Name"),
                        record_set.get("Type"),
                        record_set.get("TTL", 0),
                        values,
                    )
                )
        return records
