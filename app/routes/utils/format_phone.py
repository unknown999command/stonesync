def format_phone_number(phone):
        if phone and len(phone) == 12 and phone.startswith('+7'):
            return f"{phone[0:2]} ({phone[2:5]}) {phone[5:8]}-{phone[8:10]}-{phone[10:12]}"
        return phone