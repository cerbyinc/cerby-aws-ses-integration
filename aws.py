from boto3.session import Session

AVAILABLE_REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]


def get_client(service: str):
    """Returns an AWS Session Client based on the type argument

    Args:
        service (str): The service to use

    Returns:
        client: A valid AWS Session client
    """
    return Session().client(service)


def get_current_region() -> str:
    """Get configured Region

    Returns:
        str: The credential's configured Region
    """
    return Session().region_name


def validate_region():
    if get_current_region() not in AVAILABLE_REGIONS:
        raise Exception("Region does not support receiving email")
