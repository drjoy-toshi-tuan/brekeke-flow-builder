import type { NodeTypes } from '@xyflow/react';
import type { NodeType } from '../../ir/types';
import { NODE_CONFIG } from '../../ui/nodeConfig';
import { makeNode } from './BaseNode';

// 1 component cho mỗi NodeType (icon + màu lấy từ NODE_CONFIG), sinh tự động
// để không phải liệt kê thủ công — key khớp FlowNode.type.
export const nodeTypes: NodeTypes = Object.fromEntries(
  (Object.keys(NODE_CONFIG) as NodeType[]).map((type) => [type, makeNode(type)]),
) as Record<NodeType, NodeTypes[string]>;
