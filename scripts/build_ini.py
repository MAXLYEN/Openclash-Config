#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置构建：cfg/  ->  dist/

  cfg/    手动维护，唯一数据源，带完整注释
  dist/   自动生成，零注释，正式场景引用

设计约束（依据 subconverter/src/utils/ini_reader/ini_reader.h:253）：

  * 注释只在**行首**生效（`;` `#` `//`），且判定发生在 trimWhitespace 之后
    -> 缩进的注释算注释，可以删
    -> 行内出现的 `;` 是值的一部分，**绝不能按 `;` 截断行**
  * 空行被解析器忽略 -> 可以删
  * 整份配置严格依赖行序 -> 只做「整行保留 / 整行删除」，不排序、不去重、不合并

版本兼容：本脚本不认识任何具体分组名或规则名，只认 ini 行语法。
新增 cfg/Custom_Clash_V3.ini 后无需改脚本，构建时自动产出 dist/Custom_Clash_V3.ini。
dist/ 中源文件已消失的产物**只告警不删除** —— 那是别人还在用的订阅 URL。
"""
import os, re, sys, json, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, 'cfg')
DIST = os.path.join(ROOT, 'dist')

# 行首注释标记；与 ini_reader.h:253 保持一致
COMMENT_PREFIX = (';', '#', '//')
# 保留单行来源标记（便于在剥离后的文件里定位是哪份源文件、哪次构建）
# 设为 False 则产物零注释，来源信息只存在 dist/manifest.json
KEEP_HEADER = False


def sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def is_comment(line):
    s = line.strip()
    return bool(s) and s.startswith(COMMENT_PREFIX)


def read_normalized(path):
    """读取并规范化：去 BOM、CRLF->LF、去行尾空白、去首尾空行、结尾补换行。
    subconverter 自己会 trim，所以这些不是正确性问题，是 diff 卫生问题 ——
    行尾多一个空格会让 git diff 报变更但产物完全一致。"""
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    lines = [l.rstrip() for l in text.split('\n')]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def write_if_changed(path, content):
    if os.path.exists(path) and open(path, encoding='utf-8').read() == content:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8', newline='\n').write(content)
    return True


def stat_lines(lines):
    return {
        'ruleset':  sum(1 for l in lines if l.startswith('ruleset=')),
        'group':    sum(1 for l in lines if l.startswith('custom_proxy_group=')),
        'section':  sum(1 for l in lines if l.startswith('[') and l.endswith(']')),
    }


def main():
    if not os.path.isdir(SRC):
        sys.exit('找不到源目录：%s' % SRC)
    names = sorted(f for f in os.listdir(SRC) if f.endswith('.ini'))
    if not names:
        sys.exit('cfg/ 下没有 .ini 文件')

    manifest, src_fixed, dist_updated = {}, 0, 0
    for name in names:
        src_path = os.path.join(SRC, name)
        lines = read_normalized(src_path)

        # 就地规范化源文件
        if write_if_changed(src_path, '\n'.join(lines) + '\n'):
            src_fixed += 1
            print('  规范化源文件：%s' % name)

        # 剥离：整行判定，顺序原样
        kept = [l for l in lines if l and not is_comment(l)]
        if KEEP_HEADER:
            stamp = ';%s | built %s' % (name[:-4], datetime.date.today().isoformat())
            kept.insert(0, stamp)

        # 自检：产物与源文件在解析器眼中必须逐行等价
        # subconverter 忽略空行与行首注释，所以剥离后的有效行序列应当完全一致
        effective = [l for l in lines if l and not is_comment(l)]
        if effective != [l for l in kept if not (KEEP_HEADER and l is kept[0] and is_comment(l))]:
            sys.exit('自检失败：%s 的产物与源文件有效行不一致，构建中止' % name)

        dist_path = os.path.join(DIST, name)
        body = '\n'.join(kept) + '\n'
        if write_if_changed(dist_path, body):
            dist_updated += 1

        s = stat_lines(kept)
        manifest[name] = {
            'src_sha256':  sha256('\n'.join(lines) + '\n'),
            'dist_sha256': sha256(body),
            'src_lines':   len(lines),
            'dist_lines':  len(kept),
            'src_bytes':   len('\n'.join(lines).encode('utf-8')) + 1,
            'dist_bytes':  len(body.encode('utf-8')),
            'rulesets':    s['ruleset'],
            'groups':      s['group'],
        }
        print('%-32s %4d 行 -> %4d 行  (%d ruleset / %d group)  省 %d%%'
              % (name, len(lines), len(kept), s['ruleset'], s['group'],
                 round(100 * (1 - manifest[name]['dist_bytes'] / manifest[name]['src_bytes']))))

    # dist 中的孤儿产物：告警，不删除
    for f in sorted(os.listdir(DIST)) if os.path.isdir(DIST) else []:
        if f.endswith('.ini') and f not in names:
            print('  ⚠ dist/%s 在 cfg/ 中已无对应源文件。'
                  '未删除 —— 可能仍有订阅在引用该 URL。确认无人使用后手动删除。' % f)

    write_if_changed(os.path.join(DIST, 'manifest.json'),
                     json.dumps({'built_at': datetime.datetime.now(datetime.timezone.utc)
                                              .isoformat(timespec='seconds'),
                                 'files': manifest},
                                ensure_ascii=False, indent=2) + '\n')
    print('\n源文件规范化：%d 个    产物更新：%d 个' % (src_fixed, dist_updated))


if __name__ == '__main__':
    main()
