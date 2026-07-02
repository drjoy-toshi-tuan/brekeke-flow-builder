import { useState } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// Ô nhập điều kiện nhánh (regex). Khi KHÔNG focus, giá trị hiển thị được bọc
// ^…$ (chỉ để nhìn); khi bấm vào (focus) thì ^ $ tự mất để sửa giá trị thật.
// Giá trị lưu trong store luôn là chuỗi thô (không kèm ^ $).
// ─────────────────────────────────────────────────────────────────────────────

interface RegexBranchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function RegexBranchInput({ value, onChange, placeholder, className }: RegexBranchInputProps) {
  const [focused, setFocused] = useState(false);
  // Không focus + có giá trị -> hiển thị ^value$ (regex neo đầu/cuối).
  const display = focused || !value ? value : `^${value}$`;

  return (
    <input
      type="text"
      className={className}
      value={display}
      placeholder={placeholder}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      onChange={(e) => onChange(e.target.value)}
      spellCheck={false}
    />
  );
}
