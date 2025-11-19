import json
with open('all_lemmas.jsonl', 'r', encoding='utf-8') as f:
    line = json.loads(f.readline())
    print(f"Keys: {list(line.keys())}")
    print(f"TLA: {line['tla']}")
    print(f"HTML length: {len(line['html'])}")
    print(f"HTML sample: {line['html'][:200]}...")
