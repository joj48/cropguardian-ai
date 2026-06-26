import json

files = ['apple.json', 'tomato.json', 'potato.json', 'corn.json', 'grape.json']
fields_to_check = ['overview','symptoms','causes','infection_cycle','transmission',
                   'risk_factors','environmental_conditions','weather_influence',
                   'severity_score','immediate_actions','treatment','prevention',
                   'nutrient_management','disease_progression','recovery',
                   'economic_impact','monitoring','educational_information']

print("Field type consistency across crop files:")
print("-" * 80)

for fname in files:
    try:
        data = json.load(open(f'knowledge_base/{fname}', encoding='utf-8'))
        r = data[0]
        print(f"\n{fname} (first record: {r.get('disease_id')})")
        for f in fields_to_check:
            v = r.get(f, 'MISSING')
            t = type(v).__name__
            if isinstance(v, dict):
                keys = list(v.keys())
                print(f"  {f:<30} dict   keys={keys[:5]}")
            elif isinstance(v, list):
                inner = type(v[0]).__name__ if v else 'empty'
                print(f"  {f:<30} list   of {inner}")
            else:
                print(f"  {f:<30} {t}")
    except Exception as e:
        print(f"  ERROR reading {fname}: {e}")
