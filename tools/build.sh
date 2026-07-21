#!/usr/bin/env bash
# Пререндер страниц статей. Требует macOS (osascript/JXA) + python3.
set -euo pipefail
cd "$(dirname "$0")/.."
cat > /tmp/_dump.jxa.js <<'JXA'
ObjC.import('Foundation');
function rf(p){return ObjC.unwrap($.NSString.stringWithContentsOfFileEncodingError($(p),$.NSUTF8StringEncoding,null));}
var window={}; eval(rf('news.js'));
$.NSString.alloc.initWithUTF8String(JSON.stringify(window.NEWS)).writeToFileAtomicallyEncodingError($('/tmp/news.json'),true,$.NSUTF8StringEncoding,null);
JXA
osascript -l JavaScript /tmp/_dump.jxa.js
python3 tools/gen_articles.py /tmp/news.json
