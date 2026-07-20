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
});
