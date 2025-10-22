# dataset_builder_word_subword.py
import json
from tqdm import tqdm
from hieroglyph_tokenizer import HieroglyphTokenizer
from typing import List, Dict

class WordSubwordDatasetBuilder:
    def __init__(self, lexicon_path: str):
        self.tokenizer = HieroglyphTokenizer(lexicon_path)

    def build_dataset(self, jsonl_path: str, output_path: str, direction: str = "hg2de"):
        """
        Build dataset with full sentence input/output, but word/subword tokenized.
        """
        dataset = []

        # Count lines for tqdm
        with open(jsonl_path, "r", encoding="utf-8") as f:
            total_lines = sum(1 for _ in f)

        with open(jsonl_path, "r", encoding="utf-8") as f, \
             open(output_path, "w", encoding="utf-8") as out_f:

            for line in tqdm(f, total=total_lines, desc="Building dataset"):
                data = json.loads(line)
                hiero_sentence = data.get("hieroglyphs", "").strip()
                german_sentence = data.get("translation", "").strip()

                if not hiero_sentence or not german_sentence:
                    continue

                # --- Tokenize hieroglyphs word-by-word and subword level ---
                hg_words_tokens = [self.tokenizer.tokenize_hieroglyphs(word) for word in hiero_sentence.split()]
                hg_sentence_tokens = [tok for word in hg_words_tokens for tok in word]
                hg_sentence_string = self.tokenizer.tokens_to_string(hg_sentence_tokens)

                # --- Tokenize German sentence word-wise ---
                de_words = german_sentence.split()
                de_sentence_string = " ".join(de_words)

                # Build dataset example
                if direction == "hg2de":
                    input_text = hg_sentence_string
                    output_text = de_sentence_string
                elif direction == "de2hg":
                    input_text = de_sentence_string
                    output_text = hg_sentence_string
                else:
                    raise ValueError(f"Unknown direction {direction}")

                example = {
                    "input_text": input_text,
                    "output_text": output_text,
                    "metadata": {
                        "hieroglyph_sentence": hiero_sentence,
                        "german_sentence": german_sentence,
                        "upos": data.get("UPOS", ""),
                        "gloss": data.get("glossing", ""),
                        "lemmatization": data.get("lemmatization", "")
                    }
                }

                out_f.write(json.dumps(example, ensure_ascii=False) + "\n")
                dataset.append(example)

        print(f"Dataset saved to {output_path}, {len(dataset)} examples")


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    lexicon_path = "data/lexicon_final.json"
    corpus_path = "data/train.aegyptus"
    output_hg2de = "dataset_word_subword_hg2de.jsonl"
    output_de2hg = "dataset_word_subword_de2hg.jsonl"

    builder = WordSubwordDatasetBuilder(lexicon_path)

    # Hieroglyph -> German
    builder.build_dataset(corpus_path, output_hg2de, direction="hg2de")

    # German -> Hieroglyph
    builder.build_dataset(corpus_path, output_de2hg, direction="de2hg")
