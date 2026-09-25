# 更新记录

本模板引用的规则碎片来自 [Openclash-Rule](https://github.com/MAXLYEN/Openclash-Rule)，规则内容的更新与本模板的更新没有直接关系。

设计约定与架构说明不在本文件，见 [docs/design-notes.md](docs/design-notes.md) 与 [docs/architecture.md](docs/architecture.md)。

---

## 2026-09-24 — CI：与 Openclash-Rule 的双向通知（未升版本号，配置内容不变）

- `validate_ini.py` 新增 `--rule-ref <提交号>`：Openclash-Rule 的规则源改为按该提交从 raw 读取，报错注明「按 Rule 提交 xxxxxxx 校验」。收到 `rules-updated` 通知时传入通知里的提交号 —— 镜像约 5 分钟才同步，此前读镜像会漏过规则库刚删除或改名的文件
- 构建推送后若 `dist/Custom_Clash_V2.ini` 有变化，向 Openclash-Rule 发送 `config-updated`（携带推送后的 HEAD），触发对方的冗余分析。需配置 `RULE_DISPATCH_TOKEN`，未配置时跳过（见 [docs/操作流程.md](docs/操作流程.md) 第 7 节）

---

## 2026-09-24 — v1.x 旧配置维护（未升版本号）

- `cfg/Custom_Clash.ini` 注释掉已在规则库删除的 `BritboxUK_Domain` 引用（消除 404；其域名已由紧邻的 `UKMedia_Domain` 以同一 `UKNet` 分组覆盖，路由不变）
- 修正 `PH_Domain` 行首的 `:` 笔误为 `;` 注释（该行原本就不生效）

---

## 2026-09-24 — v2.8

- Apple AI 域名与 IP 规则集优先于普通 Apple 规则集，固定交给 `USNet`
- 英国通用规则仅引用合并后的 `UK_Domain` / `UK_IP`，保留英国媒体与 Wi-Fi Calling 专属规则
- 将 `Others_Domain` 改为 `IPCheck_Domain`，并新增 `IPCheck_IP`，沿用 `Others` 策略组
- 将暂为空的 `AppleAI_IP` / `IPCheck_IP` 纳入联网校验的预期空规则集
- 将已停用的 `OpenAI_IP` / `Copilot_IP` 纳入联网校验的预期空规则集（共用 IP 无法归属、ASN 范围过宽），保留成对引用
- 更新 BritboxUK 空占位对已删除的说明；新规则 URL 须待 Openclash-Rule 发布产物后可用
- `UK-wifi-call_Domain` 前移到 `Direct_Domain` 之前：原先 `Direct_Domain` 的 `ls.apple.com` 截走了 Apple 地区检测端点 `gspe1-ssl.ls.apple.com`，`EUNet_Domain` 截走了 `entsrv-uk.vodafone.com`，两者都到不了 `UKNet`；`UK-wifi-call_IP` 与 US / HK Wi-Fi Calling 规则无此问题，保持原位
- `ChinaMedia_Domain` 后移到 `GlobalMedia_Domain` 之后：其 `bilibili` / `qiyi` 关键字与 `iqiyi.com` 会提前吃掉 B 站国际版（`bilibili.tv`）和爱奇艺国际版（`iq.com` / `intl.iqiyi.com`），使其落入 `Domestic TV`。后移后仅 9 个国际版域名改走 `Global TV`，国内 B 站 / 爱奇艺 / 腾讯视频不受影响；`ChinaMedia_IP` 保持原位

---

## 2026-09-12 — v2.7 内调整（未升版本号）

- 地区专属区与泛分类 GEOSITE 区对调：地区文件（EUNet / UK / SG / US / JP / HK …）改为先于 `category-*` 泛分类兜底匹配
- IP 区新增 `JP_IP`，挂 `JPNet`

---

## 2026-09-06 — v2.7

- 所有规则源改走自建反代 `https://cf.210723.xyz/gh/...`（上游 `fastly.jsdelivr.net`，路径 1:1 透传），interval 统一为 3600
- 不再受 testingcf 那层 Cloudflare 12 小时缓存影响，规则送达延迟只剩 fastly（CI 会 purge）与 interval 1 小时两层

---

## 2026-09-06 — v2.6

- 规则源由「raw + 3600 / jsdelivr + 28800」改为 jsdelivr 双 CDN：`fastly` + 3600 用于自建、强制代理/直连、AI、交易所、SG 金融；`testingcf` + 28800 用于其余公共规则
- 禁止 `raw.githubusercontent.com`：OpenClash 的「Github 加速地址」会把它改写成 `@refs/heads/main`，与 CI purge 的 `@main` 不是同一个缓存键

---

## 2026-09-06 — v2.5

- 摘除 `Nintendo_IP`：其唯一一条 `IP-CIDR,35.192.0.0/12` 是 Google Cloud 的大段（约 104 万个 IP），整段判给 Game Platform 过宽，规则库已停用

---

## 2026-09-05 — v2.4

- 摘除去重后变空的三个规则集：`Steam_CDN_Domain`（被 `SteamCN_Domain` 覆盖）、`Supercell_Domain`（被 `Game_Domain` 覆盖）、`BritboxUK_Domain`（被 `UKMedia_Domain` 覆盖）

---

## 2026-09-05 — v2.3

- 撤除 `gemini.google.com` 内联修正：规则库已停用 `OpenAI_Domain` 里误收的那一条，改由 `Gemini_Domain` 正常命中（同为 `USNet`）
- `crypto.com` 内联规则保留，定位从「修正」改为不依赖 GeoSite 的显式声明（`UKNet_Domain` 里过宽的 `DOMAIN-KEYWORD,crypto` 已停用）

---

## 2026-09-05 — v2.1 ~ v2.2

- `Copilot_Domain` 改回 `OpenAI_Domain` 之后，推翻 v2.0 的前移：`Copilot_Domain` 有 26 条是 `OpenAI_Domain` 的原样复制（含 `openai.com`、`chatgpt.com`），前置会让 ChatGPT 组空转（实机日志：`chatgpt.com -> match RuleSet(Copilot_Domain) using Copilot`）
- 新增 `gemini.google.com` → `USNet` 内联修正（`OpenAI_Domain` 误收了这一条，v2.3 撤除）
- 撤除 `gstatic.com` → Google 的内联规则：它被 ⑤ 区的 `GEOSITE,google-cn` 提前命中走直连，是死规则
- v2.1 发布后曾短暂回退到 v2.0，随后以 v2.2 重新发布

---

## 2026-09-05 — v2.0

仓库从 `Custom_OpenClash_Rules` 迁移至 `Openclash-Config`，不再是上游 fork，许可证由 CC BY-SA 4.0 改为 MIT。

**策略组重构为三层架构**

- 新增地区锚点组 `USNet` / `JPNet` / `SGNet` / `AUNet` / `BRNet`，与既有的 `Proxy`(HK) / `UKNet` / `EUNet` 组成完整的一层
- 所有锚点组的第一候选改为对应节点池，全新配置或选择记录丢失时自动落在正确地区
- 平台组候选从「8 个节点池 + `.*`」改为「锚点组 + `.*`」，改一个地区的出口只需动一个组
- `Optional` 更名为 `USNet`（原名无法表达用途）；`Oceania` / `South America` 更名为 `AUNet` / `BRNet`
- `Emby` / `Google` 退回普通平台组，不再兼任日本 / 新加坡锚点
- 删除 `Asia` 组，菲律宾等无专用节点的地区统一挂靠 `JPNet`

**修复默认值全部错误**

改造前 `Proxy` 的第一候选是 `Auto-Test`（全球最低延迟，不是香港），`Optional` 的第一候选是 `Global Direct`（US_Domain / Claude / Gemini / Nvidia 全部裸连）。地区映射完全依赖手动选择维持。

**修复地区规则集吃掉平台组**

`US_Domain`(第 15 位) / `SG_Domain`(11) / `UKNet_Domain`(13) / `EUNet_Domain`(12) 原先排在平台规则之前：

- `US_Domain` 的 `DOMAIN-KEYWORD,chatgpt|copilot|claude|tiktok` 让 ChatGPT / Copilot / TikTok 三个组完全空转
- `UKNet_Domain` 的 `DOMAIN-SUFFIX,co.uk` 把 `amazon.co.uk`、`google.co.uk` 拉进 UKNet
- `SG_Domain` 的 `DOMAIN-SUFFIX,com.sg|com.my` 把 `shopee.com.sg`、`dbs.com.sg` 拉进 Cryptocurrency

地区规则集整体下沉到平台专属之后，四个组恢复工作。

**其他顺序修正**

- `Copilot_Domain` 前移到 `OpenAI_Domain` 之前（原先被吃掉 26 条）
- `PT_Domain` 前移到 `Direct_Domain` 之前（原先被吃掉 100 条）
- IP 区 `Game_IP` 下移到平台专属之后（原先吃掉 `Netflix_IP` 39 条、`Amazon_IP` 24 条）
- `Amazon_IP`（整个 AWS 地址段 1802 条）从 Shopping Platform 改挂 Proxy

**内联修正**（阶段二改规则库文件后可删除）

- `ruleset=Google,[]DOMAIN-SUFFIX,gstatic.com` —— 抢回被 `Gemini_Domain` 独占的 gstatic
- `ruleset=Cryptocurrency,[]DOMAIN-SUFFIX,crypto.com` —— 抢回被 `UKNet_Domain` 的 `DOMAIN-KEYWORD,crypto` 命中的 crypto.com

**配置改为生成式**

- `cfg/` 手动维护带注释，`dist/` 自动生成零注释，正式引用 `dist/`
- 新增 `scripts/build_ini.py`（剥离 + 规范化 + 等价性自检）与 `scripts/validate_ini.py`（结构校验 + 联网校验 provider）
- 新增 GitHub Actions 自动构建
- 删除 `Clash_Sub_Store.ini`：全部 74 条规则源 URL 已 404，72 条使用了错误的 `clash-domain` behavior，策略组停留在 V1 之前

---

## 2026-08-05 — v1.x

- 修复规则集完全不生效：补充 `clash-classic:` 前缀，并将引用切换到 YAML 格式的规则文件
- GeoSite / GeoIP 调整为兜底定位，补全至 41 条分类
- 修正 6 处检索顺序问题，消除 5 处死规则
- 重写节点正则，修复 `AU`→`AUTO`、`GB`→`100GB`、`新`→`新北` 等误匹配
- 规则集按平台拆分为 `_Domain` / `_IP` 成对结构
- 新增 PT、Instant Messaging、Social Media、Talkatone 分组
- 健康检查地址改为 `cp.cloudflare.com/generate_204`

## 2026-03-28

- 修改并补充分流规则

## 2025-01-01

- 修改规则顺序，增加分流规则，提供更细化的分流规则

## 2024-08-02

- 模板全英文化，去除所有 Emoji 图标，为 GLaDOS 机场优化模板
