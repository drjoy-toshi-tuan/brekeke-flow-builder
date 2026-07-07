import type { TKey } from '../ui/i18n';
import { GithubApiError } from './api';

// Ánh xạ lỗi (GithubApiError hoặc mã ngắn từ token store) -> key i18n để hiện thông báo.
export function ghErrorKey(input: unknown): TKey {
  const code = input instanceof GithubApiError ? input.code : String(input);
  switch (code) {
    case 'auth':
      return 'ghErrAuth';
    case 'notfound':
      return 'ghErrNotFound';
    case 'conflict':
      return 'ghErrConflict';
    case 'network':
      return 'ghErrNetwork';
    case 'ratelimit':
      return 'ghErrRateLimit';
    case 'empty':
      return 'ghErrEmpty';
    default:
      return 'ghErrOther';
  }
}
