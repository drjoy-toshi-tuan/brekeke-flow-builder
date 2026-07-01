import type { NodeTypes } from '@xyflow/react';
import type { NodeType } from '../../ir/types';
import { makeNode } from './BaseNode';

// 1 component cho mỗi NodeType, phân biệt bằng màu + icon.
// Dùng factory makeNode để mỗi type là 1 component riêng nhưng không lặp markup.
const StartNode = makeNode({ icon: '▶️', typeLabel: 'start', accent: 'border-emerald-400 bg-emerald-50', showTarget: false });
const AnnounceNode = makeNode({ icon: '🔊', typeLabel: 'announce', accent: 'border-sky-400 bg-sky-50' });
const InputNode = makeNode({ icon: '⌨️', typeLabel: 'input', accent: 'border-violet-400 bg-violet-50' });
const ConditionNode = makeNode({ icon: '🔀', typeLabel: 'condition', accent: 'border-amber-400 bg-amber-50' });
const ScriptNode = makeNode({ icon: '📜', typeLabel: 'script', accent: 'border-slate-400 bg-slate-50' });
const LlmNode = makeNode({ icon: '🤖', typeLabel: 'llm', accent: 'border-fuchsia-400 bg-fuchsia-50' });
const TransferNode = makeNode({ icon: '📞', typeLabel: 'transfer', accent: 'border-cyan-400 bg-cyan-50' });
const HangupNode = makeNode({ icon: '🛑', typeLabel: 'hangup', accent: 'border-rose-400 bg-rose-50', showSource: false });
const EndNode = makeNode({ icon: '⏹️', typeLabel: 'end', accent: 'border-gray-500 bg-gray-100', showSource: false });

// Map truyền vào React Flow. Key khớp FlowNode.type.
export const nodeTypes: NodeTypes = {
  start: StartNode,
  announce: AnnounceNode,
  input: InputNode,
  condition: ConditionNode,
  script: ScriptNode,
  llm: LlmNode,
  transfer: TransferNode,
  hangup: HangupNode,
  end: EndNode,
} satisfies Record<NodeType, NodeTypes[string]>;
