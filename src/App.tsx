import { useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import sampleYaml from '../fixtures/sample-flow.yaml?raw';
import { AuthProvider } from './auth/AuthProvider';
import { LoginScreen } from './auth/LoginScreen';
import { useAuth } from './auth/useAuth';
import { useFlowStore } from './store/flowStore';
import { FlowCanvas } from './canvas/FlowCanvas';
import { Toolbar } from './components/Toolbar';
import { NodeSettingsPanel } from './components/NodeSettingsPanel';

export default function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  );
}

// Gating: chưa đăng nhập (hoặc sai domain) -> chỉ hiện màn login.
function Gate() {
  const { user } = useAuth();
  if (!user) return <LoginScreen />;
  return <FlowApp />;
}

function FlowApp() {
  const loadYaml = useFlowStore((s) => s.loadYaml);

  // Nạp YAML mẫu khi khởi động để test UI ngay, không cần upload.
  useEffect(() => {
    void loadYaml(sampleYaml);
  }, [loadYaml]);

  return (
    <div className="flex h-full flex-col">
      <Toolbar />
      <main className="relative flex-1">
        <ReactFlowProvider>
          <FlowCanvas />
          <NodeSettingsPanel />
        </ReactFlowProvider>
      </main>
    </div>
  );
}
