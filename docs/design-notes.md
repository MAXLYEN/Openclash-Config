# 设计约定

本文件是改配置时的查阅手册，记录长期有效的约定与 subconverter / OpenClash 的行为事实。
策略组分层见 [architecture.md](architecture.md)，踩过的坑见 [troubleshooting.md](troubleshooting.md)。

---

## 一、规则与配置的分发链路

2026-09-06 起，配置与规则都经由自建反代 `cf.210723.xyz` 分发，
路由器侧只有一个恒定地址，所有切换都在服务器上完成。

### 链路

```
配置：GitHub dist/ ──定时5分钟──▶ 本地文件 ──▶ https://cf.210723.xyz
                                      └─ 缺失时回源 GitHub raw

规则：GitHub rules/yaml ──定时5分钟──▶ 本地镜像 ──▶ https://cf.210723.xyz/gh/...
                                          └─ 缺失时回源 jsdelivr
```

ini 里 117 条 provider 全部指向 `https://cf.210723.xyz/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/`，
路径与 jsdelivr 完全一致，nginx 不做改写。**interval 统一 3600**，不再按源分档。

### 为什么不直连 CDN

原先 97 条走 `testingcf.jsdelivr.net`。实测发现它是 **Cloudflare 套在 Fastly 前面**
的一层，而不是与 Fastly 并联：

```
testingcf:  cf-cache-status: HIT   Age: 10538   ← Cloudflare 直接命中自己的缓存
fastly:     X-Cache: MISS, MISS    Age: 0       ← 回源了
```

`Cache-Control: s-maxage=43200` 意味着 Cloudflare 那份副本要存 12 小时，
而 jsdelivr 的 purge API 清的是它自己的边缘（Fastly），**清不到 Cloudflare 那一层**
（purge 响应里 `CF: true` 只表示请求被接受）。所以那 97 条的实际更新延迟是
最长 12 小时 CDN + 8 小时 interval。

改走本地镜像后这一层消失，延迟只剩镜像同步周期（5 分钟）+ interval（1 小时）。

### ⚠ 不要写 raw.githubusercontent.com

OpenClash 的「Github 加速地址」会改写 provider 的 url
（`luci-app-openclash/root/usr/share/openclash/yml_rules_change.sh:295`）：
把 `raw.githubusercontent.com/用户/仓库/剩余路径` 拼成 `gh/用户/仓库@剩余路径`，
**不知道 `refs/heads/main` 应折叠成 `main`**，结果生成 `@refs/heads/main`，
与 purge 用的 `@main` 不是同一个缓存键。

`validate_ini.py` 会把 `raw.githubusercontent.com` 报为 ERROR，
并检查 provider 主机名必须是 `cf.210723.xyz`。

### 三个开关

都在服务器上，都不改变前端 URL，所以内核的 provider 缓存不会因切换而失效。
用 `clash-switch.sh` 操作：

| 开关 | 命令 | 生效方式 |
|---|---|---|
| 配置版本 | `clash-switch.sh conf prod\|debug` | 改软链，即时 |
| 规则来源 | `clash-switch.sh rule local\|upstream` | 改目录名，即时 |
| 回源上游 | `clash-switch.sh upstream fastly\|gcore\|cdn\|testingcf` | 改 nginx，自动 reload |

`clash-switch.sh status` 查看三者当前状态并实测响应头。

调试版与正式版的唯一差别是 **interval 300 vs 3600**，源已统一。

### 排查用的响应头

| 头 | 值 | 含义 |
|---|---|---|
| `X-Clash-Source` | `local` | 配置来自本地文件，正常 |
| | `github-fallback` | 本地 `current.ini` 缺失，正在回源 |
| `X-Rule-Source` | `local-mirror` | 规则来自本地镜像，正常 |
| | `jsdelivr-fallback` | 镜像缺该文件，正在回源 |

### 地址清单

| 用途 | 地址 |
|---|---|
| 配置（路由器填这个） | `https://cf.210723.xyz` |
| 配置备用 | `https://cf.210723.xyz/clash.ini` |
| 配置兜底 | `https://raw.githubusercontent.com/MAXLYEN/Openclash-Config/main/dist/Custom_Clash_V2.ini` |
| 指定版本 | `https://cf.210723.xyz/clash-prod.ini` / `clash-debug.ini` |
| 规则 | `https://cf.210723.xyz/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/<名>.yaml` |

### CI 的 purge 步骤现在管什么

构建 workflow 仍会 purge jsdelivr，但内核已不再直接读它，
所以 purge 只保证**兜底路径**的新鲜度。保留是低成本的保险，
不再是主链路的一环。

---

## 二、分组归属

- 文件名与分组名对应则用**专属分组**（`Netflix_Domain` → `Netflix`）
- 仅共用地区节点则归**地区锚点组**（`AU_Domain` → `AUNet`）
- 没有专用节点的地区挂靠到最近的锚点（菲律宾 → `JPNet`，内容并入 `JP_Domain`）

---

## 三、检索顺序

总原则：**平台维度在前，地区维度在后，ccTLD 与 gfw/cn 垫底**。

```
①  内网               private
②  自建               Self-Hosted
③  强制代理/直连      Custom_Proxy → Custom-Made → Custom_Direct
④  拦截               Reject / HDOBOXAds / TalkatoneAds
⑤  精确直连           Lan → GoogleCN → SteamCN → Steam_CDN
                      → games@cn → game-platforms-download
⑥  PT                 PT → public-tracker → PrivateTracker
⑦  泛直连             Direct_Domain → Download
⑧  平台专属           所有 XXX_Domain + 对应 GEOSITE 兜底
⑨  泛分类 GEOSITE     communication / social-media / ai / entertainment
                      / ecommerce / games / cryptocurrency
⑩  地区专属           EUNet → UKNet → SGNet → USNet → JPNet → Proxy(HK) → AUNet → BRNet
⑪  GFW 兜底           gfw → ProxyGFWlist ×3
⑫  国内兜底           China_Domain → cn
```

硬性顺序依赖（改动前务必确认）：

- **地区文件必须在平台专属之后**。放前面会吃掉平台组 —— `US_Domain` 的 AI 关键词曾让 ChatGPT / Copilot / TikTok 三个组完全空转
- **`Copilot_Domain` 必须在 `OpenAI_Domain` 之前**，否则 26 条被吃掉
- **`PT_Domain` 必须在 `Direct_Domain` 之前**，否则 100 条被吃掉
- **`SteamCN` / `Steam_CDN` 必须在 `Steam_Domain` 之前**，国区 Steam 走直连
- **IP 区的 `Game_IP` 必须在 `Netflix_IP` / `Amazon_IP` 之后**，它的段太宽

---

## 四、GeoSite / GeoIP 定位

一律作为**兜底补漏**，排在同组 `.list` 之后，由本地 list 主导匹配。

保持前置的三类例外：

1. `private` 内网
2. 国内直连类：`google-cn`、`category-games@cn`、`category-game-platforms-download`、`category-public-tracker`
3. `gfw` 与 `cn` 全局兜底（位于链尾，本身就是兜底）

---

## 五、节点正则

字母缩写统一写作 `\bXX[-_ ]?\d*\b`，可匹配 `AU` / `AU1` / `AU-01` / `AU_02`，不会误匹配 `AUTO`。

**内核是 Go RE2 引擎，不支持 `(?!...)` 与 `(?<!...)` 断言。** 写了不会报错，但正则编译失败会让整个分组变空。`validate_ini.py` 会拦下这类语法。

历史误匹配案例：`AU`→`AUTO`、`GB`→`100GB`、`新`→`新北`。

---

## 六、subconverter 行为约定

以下均来自源码，不是经验推测。

**注释语法**（`src/utils/ini_reader/ini_reader.h:253`）

```cpp
strLine = trimWhitespace(strLine);
if((!lineSize || strLine[0] == ';' || strLine[0] == '#' ||
    (lineSize >= 2 && strLine[0] == '/' && strLine[1] == '/')) && !inDirectSaveSection)
    continue;
```

- 注释标记只有 `;` `#` `//`，且**只在行首生效**
- 判定发生在 `trimWhitespace()` 之后，所以**带缩进的注释也算注释**
- **不支持行内注释**，行中间的 `;` 是值的一部分。剥离脚本只能整行删，不能按 `;` 截断
- 行尾空白与 CRLF 残留的 `\r` 会被 trim 掉，不是正确性问题

**内联规则**（`src/generator/config/ruleconvert.cpp:149`）

`ruleset=分组,[]规则` 中的 `[]` 前缀表示内联规则，原样插入不做校验。可以用它在不改规则库的前提下做定点修正：

```ini
ruleset=Google,[]DOMAIN-SUFFIX,gstatic.com
ruleset=Cryptocurrency,[]DOMAIN-SUFFIX,crypto.com
```

**空分组处理**（`src/generator/config/subexport.cpp`）

url-test 组的正则匹配不到任何节点时：

```cpp
if(filtered_nodelist.empty())
    filtered_nodelist.emplace_back("DIRECT");
```

→ 该组变成 `[DIRECT]`，**静默降级为直连，不报错**。

`groupGenerate()` 对 `[]组名` 是原样插入，不校验目标是否存在，所以引用错误只有在 Clash 加载时才暴露。

**provider 生成条件**

`ruleset=` 带了更新间隔（`,3600` / `,28800`）才生成 rule-provider，不带则内联展开。生成 provider 时必须满足：

- 前缀是 `clash-classic:`（不是 `clash-domain:`）
- 目标文件是 YAML 格式，根节点为 `payload:` 数组

纯文本 `.list` 解析不出任何内容，表现为 provider 加载成功但**规则数为 0**。详见 troubleshooting 第一节。

**外部配置格式**

subconverter 的 `&config=` 支持 ini / yaml / toml 三种格式，内容等价（`config/example_external_config.ini|yml|toml`）。本仓库只维护 ini。

---

## 七、构建约定

- `cfg/` 手动维护带注释，`dist/` 自动生成零注释，**不要直接编辑 `dist/`**
- `build_ini.py` 只做整行保留 / 整行删除，不排序、不去重、不合并 —— 整份配置的语义就是行序
- 写盘前有等价性自检：源文件与产物在解析器眼中的有效行序列必须完全一致，不一致则中止构建
- **`dist/` 中源文件已消失的产物只告警不删除** —— 那是别人订阅链接里的 URL。这一点与 Openclash-Rule 的构建策略刻意不同（那边的 yaml 是内部引用，删了无影响）
- 被注释掉的 ruleset 和备用节点池不会出现在 `dist/`，所以 **`dist/` 不能当备份用**，恢复停用的规则集要回 `cfg/` 找

---

## 八、命名与版本

- 新增版本时在 `cfg/` 放一个新 ini，构建脚本按 glob 自动产出对应的 `dist/` 文件，无需改脚本
- 淘汰旧版本时**不要删文件**，把内容改成指向新版的最小配置，避免断掉既有订阅链接
