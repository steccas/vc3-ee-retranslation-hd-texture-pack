# Tools

Source code used to build this pack. No game data, binaries, model weights, decrypted files or PNGs are
included: you need your own copies of the game, efonte's pack and the ESRGAN models.

| Folder | What it does |
|---|---|
| [`keys/`](keys/README.md) | Decrypts `DATA.BIN` (PGD → CRI CPK/CRILAYLA → GIM, plus the PAC LZ), computes PPSSPP's texture-replacement keys offline (xxh64, `ignoreAddress`), validates them against efonte's dumps, lists the textures changed by the ReTranslation and the uncovered ones, and checks every mapping of a `textures.ini`. Entry point: `keys/run_all.sh`. |
| [`upscale/`](upscale/README.md) | ESRGAN 4x upscaler that reproduces efonte's output bit-exactly (`upscale.py`), the model interpolation (`make_interp.py`), the validation against efonte's pack, the text/UI model comparison and the text/no-text selection. |

## Configuration

No path is hard-coded. Everything is set with environment variables (or CLI arguments):

| Variable | Used by | Default |
|---|---|---|
| `JP_ISO`, `EN_ISO` | `keys/run_all.sh` | required |
| `EFONTE_ZIP` | `keys/run_all.sh`, `upscale/validation/*`, `upscale/compare/build.py` | required for `run_all.sh`; elsewhere `ULJM05781_v20200807-001.zip` in the current directory |
| `PPSSPP_SRC` | `keys/run_all.sh` (builds `pgddec` against `ext/libkirk`) | required unless `keys/src/pgddec` is already built |
| `VC3_WORKDIR` | `keys/run_all.sh`, `keys/src/*` | `tools/keys/work` for `run_all.sh`; the current directory for the scripts |
| `CURRENT_INI` | `keys/run_all.sh` steps 7-8 | unset (step 8 skipped) |
| `PACK_DIR` | `keys/src/mapping_check*.py` | `$VC3_WORKDIR/pack/ULJM05957` |
| `CRILAYLA_LIB` | `keys/src/cpk.py` | `keys/src/libcrilayla.so`, pure-Python fallback |
| `KEYS_OUT` | `upscale/compare/*`, `upscale/ui_text/*` | `tools/keys/work/out` |
| `FONT` | `upscale/ui_text/*` | `DejaVuSans-Bold.ttf`, else PIL's default font |
| `PYTHON`, `CC` | `keys/run_all.sh` | `python3`, `cc` |

The `upscale/` scripts expect to be run from `tools/upscale/` (they use `models/`, `compare/`,
`validation/` and `work/` relative to it).

## Building the native helpers

```bash
cd tools/keys/src
cc -O2 -shared -fPIC -o libcrilayla.so crilayla.c
K=$PPSSPP_SRC/ext/libkirk
cc -O2 -I"$K" -o pgddec pgddec.c "$K"/amctrl.c "$K"/kirk_engine.c "$K"/AES.c "$K"/SHA1.c "$K"/bn.c "$K"/ec.c
```

`run_all.sh` does this automatically. Built files are ignored by git.

## License

GPL-3.0-or-later (see [`LICENSE`](LICENSE) and [`../LICENSES.md`](../LICENSES.md)).

The scripts were written with the help of an AI assistant (Claude) and checked against real dumps.
