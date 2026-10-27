#!/usr/bin/env bash
# Rebuild every derived artefact from the mirrored sources, then verify.
#
#   ./tools/build-all.sh
#
# 1. sources      cached downloads -> collections/scripture, collections/quran, collections/witnesses
# 2. dossier      PDF -> collections/dossier/*.md
# 3. references   PDF link annotations -> collections/references/refs.json
# 4. dossier      again, so the source-notes document carries the extracted URLs
# 5. cards        refs.json -> collections/citations/*.md
# 6. links        refs.json -> links.json, verified against document contents
# 7. catalog      filesystem + sidecars -> collections/catalog.json
# 8. site         catalog -> docs/ (static, searchable)
# 9. checks       every mirrored source contains what it claims; every link resolves
set -euo pipefail
cd "$(dirname "$0")/.."

python3 tools/fetch_web.py
python3 tools/fetch_quran.py
python3 tools/fetch_witness.py
python3 tools/make_dossier.py
python3 tools/make_references.py
python3 tools/make_dossier.py
python3 tools/make_cards.py
python3 tools/make_links.py
python3 tools/build_catalog.py
python3 tools/build_site.py
python3 tools/verify_sources.py
python3 tools/update_readme_counts.py
python3 tools/check_site.py
echo "build complete"
