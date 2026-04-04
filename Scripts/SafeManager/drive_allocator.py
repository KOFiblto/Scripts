import string
import os

def get_used_letters():
    used = []
    # Check if a drive letter is currently in use
    for letter in string.ascii_uppercase:
        # A simple check in Windows is if the path exists
        if os.path.exists(f'{letter}:\\'):
            used.append(letter)
    return used

def get_available_letters():
    used = get_used_letters()
    # Typically ignore A and B for virtual drives unless specifically requested
    return [l for l in string.ascii_uppercase if l not in used and l not in ['A', 'B']]

def allocate_drive_letter(safe, all_safes):
    available = get_available_letters()
    if not available:
        raise Exception("All drive letters A-Z are completely occupied.")

    preferred = safe.get('preferred_letter', '').upper()
    if preferred and preferred in available:
        return preferred

    other_preferred = []
    for s in all_safes:
        if s['id'] != safe['id'] and s.get('preferred_letter'):
            other_preferred.append(s['preferred_letter'].upper())

    unreserved_available = [l for l in available if l not in other_preferred]

    if unreserved_available:
        if preferred:
            closest = min(unreserved_available, key=lambda l: abs(ord(l) - ord(preferred)))
            return closest
        else:
            return unreserved_available[-1] 

    if available:
        if preferred:
            closest = min(available, key=lambda l: abs(ord(l) - ord(preferred)))
            return closest
        else:
            return available[-1]

    raise Exception("All drive letters are completely occupied.")
