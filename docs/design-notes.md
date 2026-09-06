# 设计约定

本文件是改配置时的查阅手册，记录长期有效的约定与 subconverter / OpenClash 的行为事实。
策略组分层见 [architecture.md](architecture.md)，踩过的坑见 [troubleshooting.md](troubleshooting.md)。

---

## 一、规则源分档

| 用途 | 源 | 更新间隔 | 数量 |
|---|---|---|---|
| 自建、强制代理/直连、AI、交易所、SG 金融 | `raw.githubusercontent.com/.../refs/heads/main` | `3600` | 20 |
| 其余公共规则 | `testingcf.jsdelivr.net/gh/...@main` | `28800` | 101 |

`validate_ini.py` 会检查这条约定，源与间隔不匹配会报 WARN。

### 为什么保留两个源

最初的理由是「raw 能即时生效、jsdelivr 有 CDN 缓存」。**这个理由已经不成立** ——
2026-09-05 起构建 workflow 会在推送后自动 purge 变动过的文件，jsdelivr 的 CDN
那一层延迟已经消掉；反过来 raw 自己约 5 分钟的 CDN 缓存 GitHub 不提供 purge 接口，
反而更不可控。

评估过统一到单一源，结论是**维持两源**，理由换成可用性冗余：

- 任一源出问题时，另一批规则集仍能正常更新，不会 121 个 provider 一起停摆
- `testingcf.jsdelivr.net` 是 Cloudflare 的测试端点而非官方主域 `cdn.jsdelivr.net`，
  国内可达性通常更好，但性质上是测试端点，不宜全押
- raw 在国内直连常不可达。所以走 raw 的那 20 个里包含 `Custom_Direct_Domain`、
  `SelfHosted_Domain` 是需要留意的一点：万一代理故障、raw 又拉不到，
  这批"救急用"的规则恰好更新不了。它们的内容变动很少，风险可接受，但心里要有数

**provider 拉取失败不会让已加载的规则失效** —— 内核继续用本地缓存的旧版本，
只影响"多久拿到新规则"，不影响分流本身。这是两源方案风险可控的前提。

### 真正决定生效速度的是间隔，不是源

源和间隔是两个独立维度，现在按约定捆在一起只是为了好记。给新规则集选源时按
「它属于哪一批」判断，不要再用「需不需要即时生效」当依据 —— 需不需要快由间隔决定。

### jsdelivr 缓存刷新

构建 workflow 的「刷新 jsdelivr 缓存」步骤会自动 purge 本次变动的文件。
需要手动刷时：

```
https://purge.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/文件名.yaml
```

purge 必须在 `git push` **之后**执行 —— 它会让 jsdelivr 立即回源，
推送之前回源拿到的还是旧内容。

### 备用端点

`testingcf` 出问题时可整体替换为 `fastly.jsdelivr.net` 或 `gcore.jsdelivr.net`，
是一次全局字符串替换，成本很低。

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
