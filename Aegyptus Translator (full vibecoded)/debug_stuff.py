from gardiner2unicode import GardinerToUnicodeMap

def gardiner_to_unicode(sentence: str, placeholder: str = "�") -> str:
    """
    Convert a Gardiner-coded sentence like "Aa27-W24-A24" into actual Unicode hieroglyphs.
    Unrecognized codes are replaced with `placeholder`.
    """
    g2u = GardinerToUnicodeMap()
    words = sentence.split()  # split by space between words
    unicode_sentence = []

    for word in words:
        codes = word.split('-')  # split each word into Gardiner codes
        unicode_word = ""
        for code in codes:
            char = g2u.to_unicode_hex(code)  # returns the actual Unicode character
            if char is None:
                char = placeholder
            unicode_word += char
        unicode_sentence.append(unicode_word)

    return " ".join(unicode_sentence)

# Example usage
gardiner_sentence = "Aa27-W24-A24 B27-W2-A24"
unicode_sentence = gardiner_to_unicode(gardiner_sentence)
print(unicode_sentence)  # actual hieroglyph characters, not numeric codes
