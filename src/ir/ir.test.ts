import { describe, it, expect } from 'vitest';
import { fromYaml } from './fromYaml';
import { toYaml } from './toYaml';
import { parse } from 'yaml';
import { SYNTHETIC_START_ID } from './types';

const SAMPLE = `
flow:
  name: "予約確認フロー"
  start: greet
  nodes:
    - id: greet
      type: announce
      text: "ようこそ"
      next: main_menu
    - id: main_menu
      type: input
      mode: dtmf
      prompt: "1か2を"
      next: classify
    - id: classify
      type: condition
      branches:
        - when: "input == '1'"
          to: reserve
        - when: "input == '2'"
          to: change
        - default: fallback
    - id: reserve
      type: announce
      text: "予約"
      next: end
    - id: change
      type: announce
      text: "変更"
      next: end
    - id: fallback
      type: announce
      text: "再度"
      next: main_menu
    - id: end
      type: hangup
`;

describe('fromYaml', () => {
  const ir = fromYaml(SAMPLE);

  it('tạo node start tổng hợp + node thật', () => {
    // 7 node YAML + 1 node start tổng hợp
    expect(ir.nodes).toHaveLength(8);
    expect(ir.nodes.find((n) => n.id === SYNTHETIC_START_ID)?.type).toBe('start');
  });

  it('map next thành edge default', () => {
    const e = ir.edges.find((x) => x.source === 'greet' && x.target === 'main_menu');
    expect(e?.sourceHandle).toBe('default');
  });

  it('map branches: when->to giữ condition, default là edge default', () => {
    const branchEdges = ir.edges.filter((x) => x.source === 'classify');
    expect(branchEdges).toHaveLength(3);
    expect(branchEdges.filter((x) => x.condition).length).toBe(2);
    expect(branchEdges.find((x) => x.target === 'fallback')?.condition).toBeUndefined();
  });

  it('start trỏ tới node đầu', () => {
    const startEdge = ir.edges.find((x) => x.source === SYNTHETIC_START_ID);
    expect(startEdge?.target).toBe('greet');
  });

  it('gom field lạ vào data', () => {
    const greet = ir.nodes.find((n) => n.id === 'greet');
    expect(greet?.data.text).toBe('ようこそ');
  });
});

describe('toYaml round-trip', () => {
  it('IR -> YAML tái tạo cấu trúc flow', () => {
    const ir = fromYaml(SAMPLE);
    const yaml = toYaml(ir);
    const parsed = parse(yaml) as {
      flow: {
        name: string;
        start: string;
        nodes: Array<Record<string, unknown> & { id: string; type: string }>;
      };
    };

    expect(parsed.flow.name).toBe('予約確認フロー');
    expect(parsed.flow.start).toBe('greet');
    // start tổng hợp không xuất hiện như node YAML
    expect(parsed.flow.nodes).toHaveLength(7);

    const greet = parsed.flow.nodes.find((n) => n.id === 'greet');
    expect(greet?.type).toBe('announce');
    expect(greet?.text).toBe('ようこそ');
    expect(greet?.next).toBe('main_menu');

    const classify = parsed.flow.nodes.find((n) => n.id === 'classify') as unknown as {
      branches: Array<{ when?: string; to?: string; default?: string }>;
    };
    expect(classify.branches).toHaveLength(3);
    expect(classify.branches[0]).toEqual({ when: "input == '1'", to: 'reserve' });
    expect(classify.branches[2]).toEqual({ default: 'fallback' });
  });
});
