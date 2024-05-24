import hashlib
import re


def get_username_from_mail_address(mail_address: str) -> str:
    # Convert to lower and remove characters except alphabetic
    wk = mail_address.split("@")
    local_part = wk[0].lower()
    result = re.sub(r"[^a-zA-Z0-9]", "", local_part)
    # Add top 6bytes of hash string
    md5 = hashlib.md5()
    md5.update(mail_address.encode("us-ascii"))
    h = md5.hexdigest()[0:6]
    result += "x"
    result += h
    return result
