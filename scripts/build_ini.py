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

# ---------- 调试版产物 ----------
# 除正式产物外，额外生成一份 <名称>_debug.ini，用于"改完规则想立刻看到效果"的场景。
# 与正式版的差别只有两处，都只影响送达速度，不影响任何分流行为：
#
#   1. 所有规则源改用 fastly.jsdelivr.net
#      testingcf 是 Cloudflare 套在 Fastly 前面的一层，jsdelivr 的 purge API 清不到
#      Cloudflare 那一层（实测 cf-cache-status: HIT / Age: 10538），只能等 s-maxage
#      12 小时自然过期。fastly 直连 Fastly，purge 立即生效（实测 Age: 0）。
#   2. 所有 provider 的 interval 统一压到 DEBUG_INTERVAL
#
# 调试时把 OpenClash 的订阅转换地址指向 dist/<名称>_debug.ini，调完再指回正式版。
# 注意：调试版会让每个 provider 每 DEBUG_INTERVAL 秒重新下载一次，
# 100+ 个规则集长期开着既浪费带宽也可能被 CDN 限速，用完记得切回去。
# openclash-verify.sh 的 A 段会检测并提醒当前是否处于调试版。
EMIT_DEBUG = True
DEBUG_INTERVAL = 300
DEBUG_SUFFIX = '_debug'
# 头部标了这个标记的源文件不生成调试版（已停止维护的历史版本）
SKIP_DEBUG_MARK = '已停止维护'


def make_debug(lines):
    """把正式产物的行序列改写成调试版。只动 ruleset 行的源与 interval。"""
    out, n_src, n_iv = [], 0, 0
    for l in lines:
        if l.startswith('ruleset=') and 'clash-classic:' in l:
            # 源已统一为自建反代，不再需要改写；保留计数字段以兼容输出格式
            l2 = re.sub(r',\d+$', ',%d' % DEBUG_INTERVAL, l)
            if l2 != l:
                n_iv += 1
            l = l2
        out.append(l)
    return out, n_src, n_iv


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
    # 必须按字节比较。以文本模式读取会触发 Python 的 universal newlines,
    # 把磁盘上的 CRLF 读成 LF, 于是 CRLF 源文件与 LF 规范化结果被判为"相同",
    # 规范化永远不会落盘。
    if os.path.exists(path) and open(path, 'rb').read() == content.encode('utf-8'):
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

        # 调试版产物
        dbg_note = ''
        if EMIT_DEBUG and SKIP_DEBUG_MARK not in '\n'.join(lines[:10]):
            dbg_lines, n_src, n_iv = make_debug(kept)
            dbg_name = name[:-4] + DEBUG_SUFFIX + '.ini'
            if write_if_changed(os.path.join(DIST, dbg_name),
                                '\n'.join(dbg_lines) + '\n'):
                dist_updated += 1
            dbg_note = '    + %s（源改写 %d / interval→%d）' % (dbg_name, n_src, DEBUG_INTERVAL)

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
        if dbg_note:
            print(dbg_note)

    # dist 中的孤儿产物：告警，不删除
    for f in sorted(os.listdir(DIST)) if os.path.isdir(DIST) else []:
        if f.endswith(DEBUG_SUFFIX + '.ini'):
            continue          # 调试版是派生产物，cfg/ 里本就没有对应源文件
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
