import json

with open('egyptian_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
# Find a few lemmas with definitions
for key in list(data.keys())[:10]:
    entry = data[key]
    etyms = entry.get('etymologies', [])
    if etyms:
        defn = etyms[0].get('definitions', [])
        if defn:
            d = defn[0]
            print(f"Lemma: {key}")
            print(f"  Def keys: {list(d.keys())}")
            print(f"  'definitions' field: {d.get('definitions', [])[:1]}")
            print()
