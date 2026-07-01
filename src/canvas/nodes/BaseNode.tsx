import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { RFNodeData } from '../irAdapter';

// Cấu hình hiển thị cho từng NodeType (màu/icon/nhãn loại).
export interface BaseNodeConfig {
  icon: string;
  typeLabel: string;
  // Tailwind classes cho viền + nền nhạt để phân biệt loại node.
  accent: string;
  showTarget?: boolean; // node 'start' không có input
  showSource?: boolean; // node 'hangup'/'end' không có output
}

// Factory tạo 1 component node cho mỗi NodeType từ config — tránh lặp code.
export function makeNode(config: BaseNodeConfig) {
  const showTarget = config.showTarget !== false;
  const showSource = config.showSource !== false;

  function TypedNode({ data, selected }: NodeProps) {
    const d = data as unknown as RFNodeData;
    const subtitle = pickSubtitle(d.nodeData);

    return (
      <div
        className={[
          'rounded-lg border-2 bg-white shadow-sm px-3 py-2 min-w-[180px] max-w-[240px]',
          config.accent,
          selected ? 'ring-2 ring-offset-1 ring-blue-500' : '',
        ].join(' ')}
      >
        {showTarget && <Handle type="target" position={Position.Top} />}
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">{config.icon}</span>
          <div className="min-w-0">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
              {config.typeLabel}
            </div>
            <div className="truncate text-sm font-medium text-gray-800">{d.label}</div>
          </div>
        </div>
        {subtitle && (
          <div className="mt-1 line-clamp-2 border-t border-gray-100 pt-1 text-[11px] text-gray-500">
            {subtitle}
          </div>
        )}
        {showSource && <Handle type="source" position={Position.Bottom} />}
      </div>
    );
  }

  return TypedNode;
}

// Lấy một dòng preview ngắn từ data (text/prompt/…) để hiển thị dưới label.
function pickSubtitle(data: Record<string, unknown>): string | null {
  for (const key of ['text', 'prompt', 'condition', 'mode', 'to']) {
    const value = data[key];
    if (typeof value === 'string' && value.trim()) return value;
  }
  return null;
}
