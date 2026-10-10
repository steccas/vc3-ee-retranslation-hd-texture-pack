#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Rerun the whole key pipeline. Inputs are read only; everything is written inside $VC3_WORKDIR.
#
# Required (paths to files you own; nothing is downloaded):
#   JP_ISO      Senjou no Valkyria 3 E2 - Extra Edition (Japan) ISO
#   EN_ISO      the same ISO patched with the English ReTranslation
#   EFONTE_ZIP  efonte's original pack, ULJM05781_v20200807-001.zip
#   PPSSPP_SRC  a PPSSPP source checkout (v1.20.x), used only to build pgddec against ext/libkirk
#               (not needed if src/pgddec is already built)
# Optional:
#   VC3_WORKDIR  working directory (default: tools/keys/work)
#   CURRENT_INI  textures.ini to check coverage against in steps 7-8 (e.g. the assembled pack's ini);
#                step 8 is skipped if unset
#   PYTHON       Python with xxhash, pillow, numpy (default: python3)
#   CC           C compiler (default: cc)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/src"
: "${JP_ISO:?set JP_ISO}" "${EN_ISO:?set EN_ISO}" "${EFONTE_ZIP:?set EFONTE_ZIP}"
WORK="${VC3_WORKDIR:-$HERE/work}"
PY="${PYTHON:-python3}"
CC="${CC:-cc}"
mkdir -p "$WORK"/{dec,work,out}
WORK="$(cd "$WORK" && pwd)"
export VC3_WORKDIR="$WORK"
cd "$WORK"

# 0) build the native helpers (not tracked in git)
[ -f "$SRC/libcrilayla.so" ] || "$CC" -O2 -shared -fPIC -o "$SRC/libcrilayla.so" "$SRC/crilayla.c"
if [ ! -x "$SRC/pgddec" ]; then
  : "${PPSSPP_SRC:?set PPSSPP_SRC to build pgddec}"
  K="$PPSSPP_SRC/ext/libkirk"
  "$CC" -O2 -I"$K" -o "$SRC/pgddec" "$SRC/pgddec.c" \
    "$K/amctrl.c" "$K/kirk_engine.c" "$K/AES.c" "$K/SHA1.c" "$K/bn.c" "$K/ec.c"
fi

# 1) decrypt DATA.BIN (PGD -> CPK); the vkey is recovered from the PGD header, no game key needed
if [ ! -f dec/DATA_JP.BIN ]; then
  mkdir -p iso/jp iso/en
  7z x -y -oiso/jp "$JP_ISO" PSP_GAME/INSDIR/DATA.BIN >/dev/null
  7z x -y -oiso/en "$EN_ISO" PSP_GAME/INSDIR/DATA.BIN >/dev/null
  "$SRC/pgddec" iso/jp/PSP_GAME/INSDIR/DATA.BIN dec/DATA_JP.BIN
  "$SRC/pgddec" iso/en/PSP_GAME/INSDIR/DATA.BIN dec/DATA_EN.BIN
  rm -rf iso
fi
# 2) efonte's pack: ini + original dumps only
[ -d pack/ULJM05781/original ] || unzip -o -q "$EFONTE_ZIP" 'ULJM05781/textures.ini' 'ULJM05781/original/*' -d pack
ORIG_INI="pack/ULJM05781/textures.ini"   # efonte's original textures.ini
# 3) scan GIM textures in both CPKs
"$PY" "$SRC/scan.py" dec/DATA_JP.BIN work/jp.pkl
"$PY" "$SRC/scan.py" dec/DATA_EN.BIN work/en.pkl
# 4) validation against the pack (keys + pixel content)
"$PY" "$SRC/validate.py" work/jp.pkl pack/ULJM05781
"$PY" "$SRC/packindex.py" pack/ULJM05781 work/packidx.pkl
"$PY" "$SRC/content_check.py"
# 5) EN-changed textures: list + previews
"$PY" "$SRC/cpkdiff.py" dec/DATA_JP.BIN dec/DATA_EN.BIN work/changed_files.txt
SRC="$SRC" "$PY" - <<'PYEOF'
import os, pickle, sys; sys.path.insert(0, os.environ['SRC']); import texkey
en = pickle.load(open('work/en.pkl', 'rb'))
for r in en: r['key'] = texkey.compute_key(r)
pickle.dump(en, open('work/en_keyed.pkl', 'wb'))
PYEOF
"$PY" "$SRC/export_en.py"
# 6) full key lists, ini activity for EN, alias reuse, uncovered list (against efonte's original ini)
"$PY" "$SRC/all_keys.py" dec/DATA_EN.BIN out/all_keys_en.csv work/en.pkl
"$PY" "$SRC/all_keys.py" dec/DATA_JP.BIN out/all_keys_jp.csv work/jp.pkl
"$PY" "$SRC/ini_active.py" "$ORIG_INI" out/all_keys_en.csv out/all_keys_jp.csv out/restore_spanish.txt
"$PY" "$SRC/en_reuse.py" work/jp.pkl work/en.pkl "$ORIG_INI"
"$PY" "$SRC/en_uncovered.py" "$ORIG_INI"
# 7) uncovered keys (vs CURRENT_INI if set, else vs the original ini) -> PNG per category + todo/skip
if [ -n "${CURRENT_INI:-}" ]; then "$PY" "$SRC/en_uncovered.py" "$CURRENT_INI"; fi
rm -rf out/uncovered_png && "$PY" "$SRC/export_uncovered.py" work/en.pkl
# 8) PAC textures (LZ: src/paclz.py) + palette-variant combinations vs CURRENT_INI
if [ -n "${CURRENT_INI:-}" ]; then
  rm -rf out/uncovered_pac_png out/uncovered_palvar_png
  "$PY" "$SRC/pac_palvar.py" dec/DATA_EN.BIN "$CURRENT_INI" "$ORIG_INI"
else
  echo "CURRENT_INI not set: skipped step 8 (PAC/palette-variant coverage)" >&2
fi
