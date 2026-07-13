import { describe, it, expect } from 'vitest';
import { lineMdSubset } from './iconData';

// Kiểm tra 3 icon dùng cho nút menu panel đều có trong subset offline và path hợp lệ.
describe('menu toggle icons (line-md subset)', () => {
  const names = ['menu', 'menu-to-close-transition', 'close-to-menu-transition'] as const;
  for (const name of names) {
    it(`has "${name}" with a non-empty body`, () => {
      const icon = lineMdSubset.icons[name];
      expect(icon, `icon ${name} missing`).toBeTruthy();
      expect(icon.body.length).toBeGreaterThan(0);
    });
  }

  it('transition icons morph via <animate attributeName="d">', () => {
    for (const name of ['menu-to-close-transition', 'close-to-menu-transition'] as const) {
      expect(lineMdSubset.icons[name].body).toContain('attributeName="d"');
    }
  });

  it('menu-to-close is the exact reverse of close-to-menu (same two path shapes, swapped order)', () => {
    const menuShape = 'M5 5l7 0l7 0M5 12h14M5 19l7 0l7 0';
    const closeShape = 'M5 5l7 7l7 -7M12 12h0M5 19l7 -7l7 7';
    // menu -> close: animate d from menuShape to closeShape
    expect(lineMdSubset.icons['menu-to-close-transition'].body).toContain(
      `values="${menuShape};${closeShape}"`,
    );
    // close -> menu: animate d from closeShape to menuShape
    expect(lineMdSubset.icons['close-to-menu-transition'].body).toContain(
      `values="${closeShape};${menuShape}"`,
    );
  });
});
