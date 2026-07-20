#!/usr/bin/env python3
"""連結テストBIVR ⇄ 本体BIVR の参照整合性チェック（P7 乖離検知・恵佑会札幌 260629 事故対策）。

本体BIVR（納品物）から生成した連結テストBIVR が、生成後の再編集・再生成事故で
本体と乖離していないかを機械検証する。LLM 不使用・stdlib のみ。

検証項目:
  1. ContextMatchRouter の params 完全一致（module1Name/module2Name/module*Value* 等）
     — 恵佑会事故: テストBIVR側だけ module1Name が古い TTS 参照のまま → 全ケース その他_FIXED 落ち
  2. 全モジュールの next[].nextModuleName / subs[].moduleName 一致（テスト専用 __ノードを除く）
  3. Jump to Flow の params.flowname 一致（tag プレフィックス 'T_' と 255B 短縮を除いて比較）
  4. 本体モジュールがテストBIVRに全て存在すること
  5. zip comment のソース情報（生成元 sha256）と --source-bivr の実ハッシュ突合

使い方（実機投入前の一発検証）:
  python3 connection_test/verify_test_bivr.py \
      --test-bivr output/scenarios/XX/連結テスト_XX_YYMMDD.bivr \
      --source-bivr output/scenarios/XX/XX_スクリプト版_YYMMDD.bivr [--tag T_]

差分 0 でなければ exit 1（実機投入前に再生成すること）。
stub_stt_connection.py は生成直後にこの比較を自動実行する。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

TAG_DEFAULT = "T_"
CMR_TYPE = "drjoy^Context Logic$ContextMatchRouter"
JUMP_TYPE = "drjoy^Custom Module$Custom Jump to Flow"


def short(n: str) -> str:
    return n.split("$")[-1] if n else n


def load_flows(data: bytes) -> list[dict]:
    with zipfile.ZipFile(__import__("io").BytesIO(data)) as z:
        return [json.loads(z.read(n).decode("utf-8")) for n in z.namelist()], z.comment


def strip_tag(name: str, tag: str) -> str:
    s = short(name)
    return s[len(tag):] if s.startswith(tag) else s


def match_flows(src_flows: list[dict], test_flows: list[dict], tag: str) -> tuple[dict, list]:
    """本体フロー短名 → テストフロー dict の対応表。255B 短縮は前方一致で救済。"""
    mapping, unmatched = {}, []
    test_by_stripped = {strip_tag(f.get("name", ""), tag): f for f in test_flows}
    for sf in src_flows:
        # 再スタブ（source 自体が tag 付きテストBIVR）にも対応するため source 側も tag を剥がす
        s_short = strip_tag(sf.get("name", ""), tag)
        if s_short in test_by_stripped:
            mapping[s_short] = test_by_stripped[s_short]
            continue
        # 255B 短縮: テスト側の（tag除去済み）名が本体短名の前方一致なら一意採用
        hits = [tf for stripped, tf in test_by_stripped.items()
                if stripped and s_short.startswith(stripped)]
        if len(hits) == 1:
            mapping[s_short] = hits[0]
        else:
            unmatched.append(s_short)
    return mapping, unmatched


def compare_flows(src_flows: list[dict], test_flows: list[dict], tag: str = TAG_DEFAULT) -> list[str]:
    """本体 ⇄ テストBIVR の差分リストを返す（空 = 整合）。"""
    diffs: list[str] = []
    mapping, unmatched = match_flows(src_flows, test_flows, tag)
    for u in unmatched:
        diffs.append(f"[FLOW] 本体フロー '{u}' に対応するテストフローが見つからない")

    for s_short, tf in mapping.items():
        sf = next(f for f in src_flows if strip_tag(f.get("name", ""), tag) == s_short)
        s_mods, t_mods = sf.get("modules", {}), tf.get("modules", {})

        for mn, sm in s_mods.items():
            if mn.startswith("__"):
                continue
            tm = t_mods.get(mn)
            if tm is None:
                diffs.append(f"[MODULE] {s_short}:{mn} がテストBIVRに存在しない")
                continue

            # 1. CMR params 完全一致（事故の直接原因の検知）
            if sm.get("type") == CMR_TYPE:
                sp, tp = sm.get("params", {}), tm.get("params", {})
                if tm.get("type") != CMR_TYPE:
                    diffs.append(f"[CMR] {s_short}:{mn} 型が変更されている: {tm.get('type')}")
                for k in sorted(set(sp) | set(tp)):
                    if sp.get(k) != tp.get(k):
                        diffs.append(f"[CMR] {s_short}:{mn} params.{k}: "
                                     f"本体={sp.get(k)!r} / テスト={tp.get(k)!r}")

            # 2. next 配線一致
            s_next = [n.get("nextModuleName", "") for n in sm.get("next", [])]
            t_next = [n.get("nextModuleName", "") for n in tm.get("next", [])]
            if s_next != t_next:
                diffs.append(f"[NEXT] {s_short}:{mn}: 本体={s_next} / テスト={t_next}")
            s_subs = [s.get("moduleName", "") for s in sm.get("subs", [])]
            t_subs = [s.get("moduleName", "") for s in tm.get("subs", [])]
            if s_subs != t_subs:
                diffs.append(f"[SUBS] {s_short}:{mn}: 本体={s_subs} / テスト={t_subs}")

            # 3. Jump flowname 一致（tag / 短縮を除く）
            s_fn = sm.get("params", {}).get("flowname", "")
            t_fn = tm.get("params", {}).get("flowname", "")
            if isinstance(s_fn, str) and "$" in s_fn:
                s_ref, t_ref = strip_tag(s_fn, tag), strip_tag(t_fn or "", tag)
                if s_ref != t_ref and not (t_ref and s_ref.startswith(t_ref)):
                    diffs.append(f"[JUMP] {s_short}:{mn} flowname: "
                                 f"本体={s_fn!r} / テスト={t_fn!r}")
    return diffs


def compare_bivr(src_bytes: bytes, test_path: Path, tag: str = TAG_DEFAULT) -> list[str]:
    """stub_stt_connection.py から生成直後に呼ぶ用（本体はメモリ上のバイト列）。"""
    src_flows, _ = load_flows(src_bytes)
    test_flows, _ = load_flows(test_path.read_bytes())
    return compare_flows(src_flows, test_flows, tag)


def main() -> int:
    ap = argparse.ArgumentParser(description="連結テストBIVR ⇄ 本体BIVR 整合性チェック")
    ap.add_argument("--test-bivr", required=True, help="連結テスト BIVR")
    ap.add_argument("--source-bivr", required=True, help="生成元の本体 BIVR")
    ap.add_argument("--tag", default=TAG_DEFAULT, help=f"テストフロー名プレフィックス（既定 {TAG_DEFAULT}）")
    args = ap.parse_args()

    src_path, test_path = Path(args.source_bivr), Path(args.test_bivr)
    src_bytes = src_path.read_bytes()
    src_flows, _ = load_flows(src_bytes)
    test_flows, comment = load_flows(test_path.read_bytes())

    # 5. zip comment のソース情報突合
    src_sha = hashlib.sha256(src_bytes).hexdigest()
    if comment:
        try:
            meta = json.loads(comment.decode("utf-8"))
            rec = meta.get("source_sha256", "")
            if rec and rec != src_sha:
                print(f"⚠ [SOURCE] テストBIVR は別の本体から生成されています:")
                print(f"    生成時: {meta.get('source_file', '?')} sha256={rec[:16]}…")
                print(f"    指定  : {src_path.name} sha256={src_sha[:16]}…")
            elif rec:
                print(f"✓ [SOURCE] 生成元ハッシュ一致 ({meta.get('generated_at', '?')} 生成)")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    else:
        print("ℹ [SOURCE] テストBIVR にソース情報なし（旧版 stub_stt_connection で生成）")

    diffs = compare_flows(src_flows, test_flows, args.tag)
    if diffs:
        print(f"\n!! 乖離検出: {len(diffs)} 件 — 実機投入前に再生成を推奨")
        for d in diffs:
            print(f"  {d}")
        return 1
    print(f"✓ 整合性 OK: CMR/next/subs/jump 全一致（フロー {len(src_flows)} 本）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
