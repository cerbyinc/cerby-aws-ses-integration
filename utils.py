from datetime import datetime


def prints(message: str):
    """Print a message to the stdout with the current date and time

    Args:
        message (str): The message to print to the stdout
    """
    today = datetime.today().strftime("%d/%m/%Y %H:%M:%S")
    message = f"{today}: {message}"
    print(message)


def confirm(question: str) -> bool:
    """Ask for confirmation

    Args:
        question (str): Question to confirm

    Returns:
        bool: the result based on the user chooice
    """
    question = question + " [y/n]: "
    answer = input(question)
    response = False
    while answer not in ["yes", "ye", "y", "n", "no"]:
        answer = input(question)

    if answer in ["yes", "ye", "y"]:
        response = True
    elif answer in ["no", "n"]:
        response = False

    return response


# noqa: W605,W298
def print_banner():
    """Prints an awesome banner"""
    print(
        """
                   _        
                  | |       
  ____ _____  ____| |__  _   _
 / ___) ___ |/ ___)  _ \| | | |
( (___| ____| |   | |_) ) |_| |
 \____)_____)_|   |____/ \__  |
                        (____/

Welcome to the Cerby's AWS SES Configuration tool
        """
    )


def aws_error(error: str):
    """Print a summary of the captured AWS Error

    Args:
        error (str): The error to show as summary
    """
    prints("An error occurred while processing your request,")
    print(
        """
    Please, make sure that you have the following permissions:

        AWS SES
        ses:GetIdentityDkimAttributes
        ses:SetIdentityMailFromDomain
        ses:VerifyDomainDkim

        AWS Route53
        route53:ChangeResourceRecordSets
        route53:ListHostedZonesByName
        """
    )
    print(f"Error Summary:\n\t{error}")
