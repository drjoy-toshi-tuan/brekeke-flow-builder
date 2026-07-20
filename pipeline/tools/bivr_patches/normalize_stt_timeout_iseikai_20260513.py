"""
目的: AMI Voice Timeout (timeout_ms) と DTMF Timeout (timeout) を、値が設定済みの場合のみ "30000" に統一
理由: 設計意図の変更ではない単純な値整形のため、Pattern 2 の再生成は重い。bivr_patches 規約で後処理
対象: 医誠会総合病院_診療.bivr (Downloads ディレクトリ)
ルール:
  - drjoy^AmiVoice$Speech to Text モジュール
      - params.timeout_ms が非空文字列 → "30000" に書き換え
      - 空欄は据置
  - drjoy^External Integration$DTMF AmiVoice STT Input モジュール
      - params.timeout_ms (AMI 側) が非空 → "30000"
      - params.timeout    (DTMF 側) が非空 → "30000"
      - 空欄は据置
結果 (2026-05-13 実行):
  - 実差分 4 件
      * 氏名聴取/入力_患者_氏名               AMI timeout_ms 10000 → 30000
      * 診察券番号聴取/入力_患者_診察券番号  DTMF timeout    5000 → 30000
      * 診療/折り返し_入力_復唱              DTMF timeout    5000 → 30000
      * 診療/折り返し_入力_連絡先            DTMF timeout    5000 → 30000
  - no-op 5 件 (既に 30000)
  - 空欄据置 10 件
  - 出力: 医誠会総合病院_診療_timeout30000.bivr
"""
import sys, io, json, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

SRC = Path(r"C:\Users\hamaguchi.t\Downloads\医誠会総合病院_診療.bivr")
DST = Path(r"C:\Users\hamaguchi.t\Downloads\医誠会総合病院_診療_timeout30000.bivr")

AMI_TYPES = ("drjoy^AmiVoice$Speech to Text",)
HYBRID_TYPES = ("drjoy^External Integration$DTMF AmiVoice STT Input",)


def is_nonempty(v):
    return isinstance(v, str) and v.strip() != ""


def patch_modules(data):
    """Patch modules dict in-place. Returns list of (flow, mod, field, old, new)."""
    changes = []
    flow_name = data.get("name", "")
    for mod_name, mod in data.get("modules", {}).items():
        mtype = mod.get("type", "")
        params = mod.get("params", {})
        is_hybrid = mtype in HYBRID_TYPES
        is_pure = mtype in AMI_TYPES
        if not (is_hybrid or is_pure):
            continue

        if "timeout_ms" in params and is_nonempty(params["timeout_ms"]):
            old = params["timeout_ms"]
            params["timeout_ms"] = "30000"
            tag = "30000 (no-op)" if old == "30000" else "30000"
            changes.append((flow_name, mod_name, "timeout_ms (AMI)", old, tag))

        if is_hybrid and "timeout" in params and is_nonempty(params["timeout"]):
            old = params["timeout"]
            params["timeout"] = "30000"
            tag = "30000 (no-op)" if old == "30000" else "30000"
            changes.append((flow_name, mod_name, "timeout (DTMF)", old, tag))
    return changes


def main():
    print(f"Source: {SRC}")
    print(f"Target: {DST}\n")
    all_changes = []
    with zipfile.ZipFile(SRC, "r") as zin, zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in zin.namelist():
            data = json.loads(zin.read(name).decode("utf-8"))
            all_changes.extend(patch_modules(data))
            new_text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            zout.writestr(name, new_text.encode("utf-8"))

    real = [c for c in all_changes if "no-op" not in c[4]]
    noop = [c for c in all_changes if "no-op" in c[4]]
    for c in all_changes:
        prefix = "  " if "no-op" in c[4] else "* "
        print(f"{prefix}[{c[0]}] {c[1]} :: {c[2]}  {c[3]!r} -> {c[4]!r}")
    print(f"\nReal changes: {len(real)}   No-ops: {len(noop)}")

    # Verification pass
    bad = []
    with zipfile.ZipFile(DST, "r") as z:
        for name in z.namelist():
            data = json.loads(z.read(name).decode("utf-8"))
            for mn, mod in data.get("modules", {}).items():
                mtype = mod.get("type", "")
                p = mod.get("params", {})
                if mtype not in AMI_TYPES and mtype not in HYBRID_TYPES:
                    continue
                ami = p.get("timeout_ms", "")
                if is_nonempty(ami) and ami != "30000":
                    bad.append((mn, "AMI", ami))
                if mtype in HYBRID_TYPES:
                    dtmf = p.get("timeout", "")
                    if is_nonempty(dtmf) and dtmf != "30000":
                        bad.append((mn, "DTMF", dtmf))
    if bad:
        print(f"\n!! VERIFICATION FAILED: {bad}")
        sys.exit(1)
    print(f"\nVerification OK. Output: {DST}")


if __name__ == "__main__":
    main()
