import { useCallback, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge as rfAddEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
  type NodeMouseHandler,
} from '@xyflow/react';
import { useFlowStore } from '../store/flowStore';
import { irToReactFlow } from './irAdapter';
import { nodeTypes } from './nodes';
import { edgeTypes } from './edges/DeletableEdge';

// ─────────────────────────────────────────────────────────────────────────────
// Canvas React Flow. IR là source of truth:
//   - Render nodes/edges TỪ IR (re-derive mỗi khi IR đổi: load / auto-layout / sửa panel).
//   - React Flow xử lý tương tác mượt (kéo, chọn vùng, zoom) trên state cục bộ,
//     rồi commit các thay đổi có nghĩa (kéo xong, nối, xoá) trở lại IR store.
// ─────────────────────────────────────────────────────────────────────────────

export function FlowCanvas() {
  const ir = useFlowStore((s) => s.ir);
  const setNodePositions = useFlowStore((s) => s.setNodePositions);
  const addEdge = useFlowStore((s) => s.addEdge);
  const selectNode = useFlowStore((s) => s.selectNode);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Re-derive trạng thái canvas mỗi khi IR đổi (state -> view, một chiều).
  useEffect(() => {
    if (!ir) return;
    const rf = irToReactFlow(ir);
    setNodes(rf.nodes);
    setEdges(rf.edges);
  }, [ir, setNodes, setEdges]);

  // Kéo xong 1 node -> commit vị trí vào IR (để auto-layout/re-derive không mất chỗ).
  const onNodeDragStop = useCallback(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    for (const n of nodes) positions[n.id] = n.position;
    setNodePositions(positions);
  }, [nodes, setNodePositions]);

  // Nối dây -> thêm edge vào state cục bộ + commit vào IR.
  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      const id = `${connection.source}->${connection.target}#${Date.now()}`;
      setEdges((eds) => rfAddEdge({ ...connection, id, type: 'deletable' }, eds));
      addEdge({
        id,
        source: connection.source,
        target: connection.target,
        sourceHandle: connection.sourceHandle ?? undefined,
      });
    },
    [setEdges, addEdge],
  );

  // Double-click node -> mở panel setting.
  const onNodeDoubleClick: NodeMouseHandler = useCallback(
    (_event, node) => selectNode(node.id),
    [selectNode],
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeDragStop={onNodeDragStop}
      onConnect={onConnect}
      onNodeDoubleClick={onNodeDoubleClick}
      onPaneClick={() => selectNode(null)}
      selectionOnDrag
      multiSelectionKeyCode={['Meta', 'Shift']}
      fitView
      proOptions={{ hideAttribution: true }}
    >
      <Background gap={16} />
      <Controls />
      <MiniMap pannable zoomable />
    </ReactFlow>
  );
}
