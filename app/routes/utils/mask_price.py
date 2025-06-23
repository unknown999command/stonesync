import re

def mask_price_and_prepayment(message):
    pattern = r'(Цена: )(.+?)(\n|$)|(Предоплата: )(.+?)(\n|$)'
    def replace_with_stars(match):
        if match.group(1):
            return f"{match.group(1)}{'*' * len(match.group(2))}{match.group(3)}"
        elif match.group(4):
            return f"{match.group(4)}{'*' * len(match.group(5))}{match.group(6)}"
        return match.group(0)
    cleaned_message = re.sub(pattern, replace_with_stars, message)
    return cleaned_message.strip()