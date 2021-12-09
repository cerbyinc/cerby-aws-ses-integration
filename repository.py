from typing import List, Optional

from aws import get_client
from models import HostedZoneRecord, Identity


class AWSIdentityRepository:
    def __init__(self) -> None:
        super().__init__()
        self.client = get_client("ses")

    def add(self, new: Identity) -> Identity:
        identity = self.get(new.name)
        if identity:
            new = identity
        else:
            response = self.client.verify_domain_dkim(Domain=new.name)
            new.dkim_tokens = response["DkimTokens"]
            new.verification_status = "Pending"
        return new

    def get(self, name: str) -> Optional[Identity]:
        identities = self.client.get_identity_dkim_attributes(Identities=[name])
        if name in identities["DkimAttributes"]:
            attributes = identities["DkimAttributes"][name]
            return Identity(
                name, attributes["DkimTokens"], attributes["DkimVerificationStatus"]
            )
        else:
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

    def add(self, record: HostedZoneRecord):
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
            HostedZoneId=record.hosted_zone_id,
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
            for resource_record in record_set["ResourceRecords"]:
                values.append(resource_record["Value"])
            records.append(
                HostedZoneRecord(
                    hosted_zone_id,
                    record_set["Name"],
                    record_set["Type"],
                    record_set["TTL"],
                    values,
                )
            )
        return records
