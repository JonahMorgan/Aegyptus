# example_run.py
from hieroglyph_tokenizer import HieroglyphTokenizer

def example():
    # Load tokenizer with your lexicon
    tokenizer = HieroglyphTokenizer("data/lexicon_final.json")

    # Example hieroglyphic sentence (space-separated words)
    hiero_sentence = "𓅱𓂧𓎡𓄿 𓂓𓏏𓈖𓈖"
    print("=== Hieroglyphic input ===")
    tokens = tokenizer.tokenize_hieroglyphs(hiero_sentence)
    for t in tokens:
        print(t)
    print("Model input string:", tokenizer.tokens_to_string(tokens))

    # Example transliteration sentence
    translit_sentence = "wdi̯.kꜣ kt.t"
    print("\n=== Transliteration input ===")
    tokens_translit = tokenizer.tokenize_transliteration(translit_sentence)
    for t in tokens_translit:
        print(t)
    print("Model input string:", tokenizer.tokens_to_string(tokens_translit))

if __name__ == "__main__":
    example()