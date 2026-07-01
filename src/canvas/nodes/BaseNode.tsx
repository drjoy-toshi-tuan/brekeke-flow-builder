import type { CSSProperties } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { RFNodeData } from '../irAdapter';
import type { NodeType } from '../../ir/types';
import { NODE_CONFIG } from '../../ui/nodeConfig';
import { Icon } from '../../ui/icons';

// ─────────────────────────────────────────────────────────────────────────────
// Node card. Bố cục theo yêu cầu:
//   - Bên phải: icon của loại node (tile màu accent).
//   - Bên trái xếp dọc: (trên) tên LOẠI module · (giữa) TÊN module · (dưới) mô tả.
// Màu accent lấy từ NODE_CONFIG, truyền vào CSS qua biến --accent.
// ─────────────────────────────────────────────────────────────────────────────

// Factory tạo 1 component node cho mỗi NodeType — tránh lặp markup.
export function makeNode(nodeType: NodeType) {
  const cfg = NODE_CONFIG[nodeType];
  const showTarget = cfg.showTarget !== false;
  const showSource = cfg.showSource !== false;

  function TypedNode({ data, selected }: NodeProps) {
    const d = data as unknown as RFNodeData;
    const description = pickDescription(d.nodeData);

    return (
      <div
        className={['bk-node', selected ? 'bk-node--selected' : ''].join(' ')}
        style={{ '--accent': cfg.color } as CSSProperties}
      >
        {showTarget && <Handle type="target" position={Position.Top} className="bk-handle" />}

        <div className="bk-node-body">
          <div className="bk-node-text">
            <div className="bk-node-type">{cfg.typeLabel}</div>
            <div className="bk-node-name" title={d.label}>
              {d.label}
            </div>
            {description ? (
              <div className="bk-node-desc" title={description}>
                {description}
              </div>
            ) : (
              <div className="bk-node-desc bk-node-desc--empty">Chưa có mô tả</div>
            )}
          </div>
          <div className="bk-node-icon">
            <Icon icon={cfg.icon} />
          </div>
        </div>

        {showSource && <Handle type="source" position={Position.Bottom} className="bk-handle" />}
      </div>
    );
  }

  return TypedNode;
}

// Mô tả là field do người dùng tự nhập (data.description). Không lấy text/prompt
// làm mô tả — những field đó chỉ sửa trong panel setting.
function pickDescription(data: Record<string, unknown>): string | null {
  const value = data.description;
  return typeof value === 'string' && value.trim() ? value : null;
}
