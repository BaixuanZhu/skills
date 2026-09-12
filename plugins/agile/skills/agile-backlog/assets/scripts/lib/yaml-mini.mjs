// yaml-mini.mjs —— 最小 YAML 解析器（仅覆盖 backlog schema 子集）
//
// 支持:标量(string/number/bool/null)+ 单行数组 [a, b, "c", 1] + 嵌套 map
//       + 数组项是 map - key: value + # 注释 + '...' / "..." 引号字符串。
//
// 已知 Backlog YAML 用例:items[] 每项是 map,adr_refs 是字符串数组。
//
// 零外部依赖(只 import node 内置模块时由调用方负责)。
//
// 用法:
//   import { yamlParse } from './lib/yaml-mini.mjs';
//   const data = yamlParse(text);

export function yamlParse(text) {
  const raw = text.split(/\r?\n/)
    .map(l => l.replace(/\s*#.*$/, ''))
    .map(l => l.replace(/\s+$/, ''))
    .filter(l => l.length > 0);

  let pos = 0;

  function parseScalar(s) {
    s = s.trim();
    if (s === '' || s === '~' || s === 'null' || s === 'Null' || s === 'NULL') return null;
    if (s === 'true' || s === 'True' || s === 'TRUE') return true;
    if (s === 'false' || s === 'False' || s === 'FALSE') return false;
    if (/^-?\d+$/.test(s)) return Number(s);
    if (/^-?\d+\.\d+$/.test(s)) return Number(s);
    if (s.startsWith('"') && s.endsWith('"') && s.length >= 2) {
      return s.slice(1, -1).replace(/\\(["\\nrt])/g, (_, c) => ({'"':'"','\\':'\\','n':'\n','r':'\r','t':'\t'}[c]));
    }
    if (s.startsWith("'") && s.endsWith("'") && s.length >= 2) {
      return s.slice(1, -1).replace(/''/g, "'");
    }
    return s;
  }

  function parseInlineArray(s) {
    s = s.trim();
    if (!s.startsWith('[') || !s.endsWith(']') || s.length < 2) return null;
    s = s.slice(1, -1).trim();
    if (s === '') return [];
    return s.split(',').map(part => parseScalar(part.trim()));
  }

  function indentOf(line) {
    let n = 0;
    while (n < line.length && line[n] === ' ') n++;
    return n;
  }

  function parseBlockMap(indent) {
    const out = {};
    while (pos < raw.length) {
      const line = raw[pos];
      const ind = indentOf(line);
      if (ind < indent) break;
      if (ind > indent) { pos++; continue; }
      // array 项起首 → 必须退出,留给 parseBlockArray 接管
      if (line.trimStart().startsWith('- ')) break;
      // 兼容行内缩进(典型 item 行有 2 空格缩进 + `key:`)
      const m = line.match(/^\s*([^:]+):\s*(.*)$/);
      if (!m) { pos++; continue; }
      const key = m[1].trim();
      const rest = m[2].trim();
      if (rest === '') {
        pos++;
        if (pos < raw.length && indentOf(raw[pos]) > ind) {
          const subInd = indentOf(raw[pos]);
          if (raw[pos].trimStart().startsWith('- ')) {
            out[key] = parseBlockArray(subInd);
          } else {
            out[key] = parseBlockMap(subInd);
          }
        } else {
          out[key] = null;
        }
      } else if (rest.startsWith('[') && rest.endsWith(']')) {
        out[key] = parseInlineArray(rest);
        pos++;
      } else {
        out[key] = parseScalar(rest);
        pos++;
      }
    }
    return out;
  }

  function parseBlockArray(indent) {
    const arr = [];
    while (pos < raw.length) {
      const line = raw[pos];
      const ind = indentOf(line);
      if (ind < indent) break;
      if (ind > indent) { pos++; continue; }
      // 必须 \s* 兼容 array 项前的缩进(典型 2 空格 + `- `)
      const m = line.match(/^\s*-\s+(.*)$/);
      if (!m) { pos++; continue; }
      pos++;
      const rest = m[1].trim();
      if (rest === '') {
        if (pos < raw.length && indentOf(raw[pos]) > indent) {
          arr.push(parseBlockMap(indentOf(raw[pos])));
        } else {
          arr.push(null);
        }
      } else if (rest.startsWith('[') && rest.endsWith(']')) {
        arr.push(parseInlineArray(rest));
      } else if (rest.includes(':')) {
        const sub = {};
        const firstM = rest.match(/^([^:]+):\s*(.*)$/);
        if (firstM) {
          const v = firstM[2].trim();
          if (v.startsWith('[') && v.endsWith(']')) sub[firstM[1].trim()] = parseInlineArray(v);
          else sub[firstM[1].trim()] = v === '' ? null : parseScalar(v);
        }
        while (pos < raw.length) {
          const l2 = raw[pos];
          const ind2 = indentOf(l2);
          if (ind2 <= indent) break;
          // array 项起首 → 单层 map 项到此结束,留给 parseBlockArray 下一轮
          if (l2.trimStart().startsWith('- ')) break;
          const m2 = l2.match(/^\s*([^:]+):\s*(.*)$/);
          if (!m2) { pos++; continue; }
          const v2 = m2[2].trim();
          if (v2.startsWith('[') && v2.endsWith(']')) sub[m2[1].trim()] = parseInlineArray(v2);
          else sub[m2[1].trim()] = v2 === '' ? null : parseScalar(v2);
          pos++;
        }
        arr.push(sub);
      } else {
        arr.push(parseScalar(rest));
      }
    }
    return arr;
  }

  return parseBlockMap(0);
}
