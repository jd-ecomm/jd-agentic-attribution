"""Update data/searchable.json from a pull_searchable.js result (JSON). Usage: python3 tools/merge_searchable.py data/searchable.json sv.json"""
import json,sys
cur=json.load(open(sys.argv[1]));new=json.load(open(sys.argv[2]))
assert new['weekly'] and new['rank']['7d'], 'empty Searchable pull'
assert any(r[0]=='JD Sports' for r in new['rank']['7d']), 'JD missing from ranking'
cur.update(pulled=new['pulled'],weekly=new['weekly'],rank=new['rank'])
json.dump(cur,open(sys.argv[1],'w'),indent=0)
print('searchable', new['pulled'], 'weeks', len(new['weekly']), 'JD 7d', [r for r in new['rank']['7d'] if r[0]=='JD Sports'][0])
