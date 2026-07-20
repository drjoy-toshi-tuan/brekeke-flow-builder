import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { parse } from 'yaml';
import { fromDesignYaml } from './fromDesignYaml';
import { toDesignYaml } from './toDesignYaml';

const FIXTURE_PATH = new URL('../../../fixtures/design-flow-proto.yaml', import.meta.url);

describe('designYaml adapter', () => {
  it('parses scenario_flow steps into IR nodes/edges', () => {
    const text = readFileSync(FIXTURE_PATH, 'utf-8');
    const { ir, passthrough } = fromDesignYaml(text, { id: 'proto-flat', name: 'プロト_フラット' });

    expect(ir.nodes.map((n) => n.id)).toEqual(['冒頭', '冒頭_アナウンス', '氏名聴取', '生年月日聴取', '電話番号聴取', '終了']);
    expect(ir.nodes.find((n) => n.id === '氏名聴取')).toMatchObject({
      type: 'interaction',
      data: { blockType: 'slot', slot: 'patient_name', save_to: 'patientName' },
    });
    expect(ir.edges).toContainEqual(
      expect.objectContaining({ source: '冒頭', target: '冒頭_アナウンス', sourceHandle: 'default' }),
    );
    // Section không phải graph phải giữ nguyên ở passthrough.
    expect(passthrough.basic_info).toBeDefined();
    expect(passthrough.termination_patterns).toBeDefined();
    expect(passthrough.scenario_flow).toBeUndefined();
  });

  it('round-trips: fromDesignYaml -> toDesignYaml giữ nguyên nội dung nghiệp vụ (diff = 0 khi không sửa gì)', () => {
    const text = readFileSync(FIXTURE_PATH, 'utf-8');
    const { ir, passthrough } = fromDesignYaml(text, { id: 'proto-flat', name: 'プロト_フラット' });
    const out = toDesignYaml(ir, passthrough);

    const originalDoc = parse(text);
    const roundTripDoc = parse(out);

    expect(roundTripDoc.scenario_flow).toEqual(originalDoc.scenario_flow);
    expect(roundTripDoc.termination_patterns).toEqual(originalDoc.termination_patterns);
    expect(roundTripDoc.basic_info).toEqual(originalDoc.basic_info);
    expect(roundTripDoc.context_fields).toEqual(originalDoc.context_fields);
    expect(roundTripDoc.hearing_items).toEqual(originalDoc.hearing_items);
  });

  it('nhánh rẽ (conditions) -> data.branches để dùng editor nhánh có sẵn của canvas, và round-trip lại đúng', () => {
    const text = [
      'scenario_flow:',
      '  - step: "用件確認"',
      '    type: hearing',
      '    output_format: enum',
      '    output_labels:',
      '      - "予約"',
      '      - "変更"',
      '    conditions:',
      '      - match: "予約"',
      '        next: "予約フロー"',
      '      - match: "変更"',
      '        next: "変更フロー"',
      '      - match: "default"',
      '        next: "失敗フロー"',
      '  - step: "予約フロー"',
      '    type: termination',
      '    termination_ref: "END_予約"',
      '  - step: "変更フロー"',
      '    type: termination',
      '    termination_ref: "END_変更"',
      '  - step: "失敗フロー"',
      '    type: termination',
      '    termination_ref: "END_失敗"',
      '',
    ].join('\n');

    const { ir, passthrough } = fromDesignYaml(text, { id: 'x', name: 'x' });
    const hearingNode = ir.nodes.find((n) => n.id === '用件確認');
    expect(hearingNode?.type).toBe('interaction'); // hearing -> interaction, KHÔNG có data.branches (không phải EDITABLE_BRANCH_TYPES)

    // Edge vẫn dựng đúng dù node type không dùng editor nhánh của canvas.
    expect(ir.edges).toContainEqual(
      expect.objectContaining({ source: '用件確認', target: '予約フロー', condition: '予約' }),
    );
    expect(ir.edges).toContainEqual(
      expect.objectContaining({ source: '用件確認', target: '失敗フロー', sourceHandle: 'default' }),
    );

    const out = toDesignYaml(ir, passthrough);
    const roundTripDoc = parse(out);
    const originalDoc = parse(text);
    expect(roundTripDoc.scenario_flow).toEqual(originalDoc.scenario_flow);
  });
});
