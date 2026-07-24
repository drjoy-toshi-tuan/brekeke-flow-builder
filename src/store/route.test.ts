import { describe, it, expect } from 'vitest';
import { parseHash, serializeRoute, type RouteState } from './route';

describe('route parseHash', () => {
  it('rỗng -> ts / flow-management', () => {
    expect(parseHash('')).toEqual({ mode: 'ts', screen: 'flow-management', fileId: null, tab: null });
    expect(parseHash('#')).toEqual({ mode: 'ts', screen: 'flow-management', fileId: null, tab: null });
    expect(parseHash('#/')).toEqual({ mode: 'ts', screen: 'flow-management', fileId: null, tab: null });
  });

  it('hash cũ #/cs | #/ts -> flow-management', () => {
    expect(parseHash('#/cs')).toEqual({ mode: 'cs', screen: 'flow-management', fileId: null, tab: null });
    expect(parseHash('#/ts')).toEqual({ mode: 'ts', screen: 'flow-management', fileId: null, tab: null });
  });

  it('flow-management tường minh', () => {
    expect(parseHash('#/cs/flow-management')).toEqual({
      mode: 'cs',
      screen: 'flow-management',
      fileId: null,
      tab: null,
    });
  });

  it('file có id, không tab', () => {
    expect(parseHash('#/ts/file/ABC123')).toEqual({
      mode: 'ts',
      screen: 'file',
      fileId: 'ABC123',
      tab: null,
    });
  });

  it('file có id + tab', () => {
    expect(parseHash('#/cs/file/ABC123/announce')).toEqual({
      mode: 'cs',
      screen: 'file',
      fileId: 'ABC123',
      tab: 'announce',
    });
  });

  it('file thiếu id -> flow-management', () => {
    expect(parseHash('#/cs/file')).toEqual({
      mode: 'cs',
      screen: 'flow-management',
      fileId: null,
      tab: null,
    });
  });

  it('mode lạ -> mặc định ts', () => {
    expect(parseHash('#/xx/file/ID').mode).toBe('ts');
  });

  it('giải mã id chứa ký tự đặc biệt', () => {
    expect(parseHash('#/cs/file/a%2Fb').fileId).toBe('a/b');
  });
});

describe('route serializeRoute', () => {
  it('flow-management', () => {
    expect(serializeRoute({ mode: 'cs', screen: 'flow-management', fileId: null, tab: null })).toBe(
      '#/cs/flow-management',
    );
  });

  it('file không tab', () => {
    expect(serializeRoute({ mode: 'ts', screen: 'file', fileId: 'ABC', tab: null })).toBe('#/ts/file/ABC');
  });

  it('file + tab', () => {
    expect(serializeRoute({ mode: 'cs', screen: 'file', fileId: 'ABC', tab: 'general' })).toBe(
      '#/cs/file/ABC/general',
    );
  });

  it('screen=file nhưng thiếu id -> flow-management (không sinh URL hỏng)', () => {
    expect(serializeRoute({ mode: 'cs', screen: 'file', fileId: null, tab: 'announce' })).toBe(
      '#/cs/flow-management',
    );
  });
});

describe('route round-trip', () => {
  const cases: RouteState[] = [
    { mode: 'cs', screen: 'flow-management', fileId: null, tab: null },
    { mode: 'ts', screen: 'file', fileId: 'ABC123', tab: null },
    { mode: 'cs', screen: 'file', fileId: 'ABC123', tab: 'status' },
  ];
  for (const r of cases) {
    it(`serialize->parse giữ nguyên: ${serializeRoute(r)}`, () => {
      expect(parseHash(serializeRoute(r))).toEqual(r);
    });
  }
});
