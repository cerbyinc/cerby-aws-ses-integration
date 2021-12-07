from dataclasses import dataclass
from typing import List


@dataclass
class Identity:
    name: str
    dkim_tokens: List[str] = None
    verification_status: str = None

    def dkim_tokens_as_records(self, hosted_zone_id: str, domain: str):
        records: list = []
        for dkim_token in self.dkim_tokens:
            records.append(
                HostedZoneRecord(
                    hosted_zone_id,
                    f"{dkim_token}._domainkey.{domain}",
                    "CNAME",
                    300,
                    [f"{dkim_token}.dkim.amazonses.com"],
                )
            )
        return records


@dataclass
class HostedZoneRecord:
    hosted_zone_id: str
    name: str
    type: str
    ttl: int = 300
    values: List[str] = None

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HostedZoneRecord):
            return False
        if (
            self.hosted_zone_id == __o.hosted_zone_id
            and __o.name in self.name
            and self.type == __o.type
        ):
            return True
        return False

    def __hash__(self):
        return hash(self.hosted_zone_id + self.name + self.type)
