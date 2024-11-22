from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DkimAttributes:
    name: str
    verification_status: str = "Pending"
    dkim_tokens: List[str] = field(default_factory=list)

    def dkim_tokens_as_records(self, domain: str):
        records: list = []
        for dkim_token in self.dkim_tokens:
            records.append(
                HostedZoneRecord(
                    f"{dkim_token}._domainkey.{domain}",
                    "CNAME",
                    300,
                    [f"{dkim_token}.dkim.amazonses.com"],
                )
            )
        return records


@dataclass
class MailFromDomainAttributes:
    name: str
    mail_from_domain: str
    behavior_on_mx_failure: str = "UseDefaultValue"
    mail_from_domain_status: Optional[str] = None


@dataclass
class HostedZoneRecord:
    name: str
    type: str
    ttl: int = 300
    values: List[str] = field(default_factory=list)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HostedZoneRecord):
            return False
        if __o.name in self.name and self.type == __o.type:
            return True
        return False

    def __hash__(self):
        return hash(self.name + self.type)
