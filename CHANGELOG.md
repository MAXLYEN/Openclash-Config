# 更新记录

本模板引用的规则碎片来自 [Openclash-Rule](https://github.com/MAXLYEN/Openclash-Rule)，规则内容的更新与本模板的更新没有直接关系。

设计约定与架构说明不在本文件，见 [docs/design-notes.md](docs/design-notes.md) 与 [docs/architecture.md](docs/architecture.md)。

---

## 2026-09-26 — v2.12

- Meta 的 `GEOIP,facebook` 改为 `USNet`，使无域名元数据的 Meta IP 连接使用美国出口
- 在通用通信与社交 GeoSite 前增加 `GEOSITE,meta` → `USNet`，补齐 `US_Domain` 未列出的一方域名；已列出的域名仍优先由 Rule provider 命中
- OpenAI、Claude、Gemini、GitHub 与各地区 provider 的引用和顺序保持现有配置；新增编程模型域名由 Openclash-Rule 对应列表提供

---

## 2026-09-25 — v2.11

引用 Openclash-Rule `7e62bd7` 新增的两个规则集，把 v2.10 撤除内联规则后遗留的归属问题在规则内容层面补回：

- 新增 `CryptoCom_Domain` → Cryptocurrency，排在 ⑧ 金融区 `OKX_Domain` 之前。`crypto.com` 已从 `SG_Domain` 停用，此前由 ⑩ 区 `GEOSITE,category-cryptocurrency` 兜底进 Cryptocurrency（结果正确但依赖 geodata），现由规则集直接命中
- 新增 `HuluJP_Domain` → JPNet，排在 `Hulu_Domain` / `GEOSITE,disney` 之前。日本 Hulu 需要日本 IP，此前 `hulu.jp` 落到 `GEOSITE,disney`（Disney+），`happyon.jp`、`hjholdings.jp`、`streaks.jp`、`yb.uncn.jp`、`prod.hjholdings.tv` 落到 `GlobalMedia_Domain`（Global TV），都不是日本出口。这 6 条已从 `Hulu_Domain` 停用
- 成对的 `CryptoCom_IP` / `HuluJP_IP` 是空占位，按 `OKX_IP` / `Bybit_IP` / `Hulu_IP` / `Disney_IP` 的惯例不引用
- `docs/design-notes.md` 第三节补充两条顺序依赖；`docs/troubleshooting.md` 验证清单更新 `crypto.com`，新增 `www.hulu.jp`

---

## 2026-09-25 — v2.10

明确分工：本仓库只决定规则顺序与引用哪些规则集，域名 / IP 等规则内容一律放 Openclash-Rule。

- 撤除全部内联内容规则：`[]DOMAIN-SUFFIX,crypto.com`（Cryptocurrency）与 v2.9 新加的 `[]DOMAIN,notnetflix.cos.cat`（Emby）。撤除后 `crypto.com` 由 `SG_Domain` 命中走 SGNet（与 Cryptocurrency 的默认出口相同，只是不再跟随 Cryptocurrency 组切换），`notnetflix.cos.cat` 回到 Netflix 组；两者的正确归属交由 Openclash-Rule 在规则内容层面解决，需要新规则集时再回到本仓库引用
- `validate_ini.py` 新增检查：`[]` 内联只允许 `GEOSITE` / `GEOIP` / `FINAL` / `MATCH`，其他类型报 ERROR
- `cfg` 头部新增【分工】说明；`docs/design-notes.md` 的「内联规则」一节改为禁止写内容规则，删除 v2.9 加的 notnetflix 顺序依赖；`docs/troubleshooting.md` 的 `crypto.com` 期望命中同步为现状

---

## 2026-09-25 — v2.9

规则覆盖复查（把链上 GEOSITE 按 MetaCubeX 文本版展开做首命中模拟，与 Openclash-Rule 同日的复查一致）。按全部已知域名比对前后首命中，只有下列 646 个域名换组：

- ⚠ ⑩ 区改用 `GEOSITE,category-games-!cn`：该分类 v2fly 自 2025-06-05 起才有（Loyalsoldier / MetaCubeX 当前的 geosite.dat 均已包含），路由器的 geosite.dat 早于此时整份配置会加载失败，更新订阅前先更新 GeoSite 数据库
- `category-games` 改为 `category-games-!cn`：原分类里的国内游戏站（`17173.com`、`4399.com`、`37.com`、`3304399.net` 等）没有 `@cn` 属性，⑤ 区的 `category-games@cn` 截不住，此前走 Game Platform（默认香港）。现在 237 个改走直连（193 个由 `GEOSITE,cn`、44 个由 `China_Domain` 命中），另有 5 个不在国内列表里的落到 FINAL、1 个（`bx.in.th`）落到 `GEOSITE,gfw`
- `Hulu_Domain` 前移到 `Disney_Domain` / `GEOSITE,disney` 之前：geosite:disney 收录了全部 Hulu 域名，`Disney_Domain` 也有 `hulu.playback.edge.bamgrid.com`，此前 Hulu 组完全空转，`hulu.com` 等 49 个域名走 Disney+ 组（默认香港），而 Hulu 只在美国可用。Disney 本身的域名去向不变
- ⑩ 泛分类区游戏分类（现为 `category-games-!cn`）移到 `category-entertainment` 之前：后者收录了 `category-games` 1123 条中的 859 条，此前本地游戏列表未收录的 353 个游戏域名（`epicgamescdn.com`、`diablo.com`、`ubistatic*-a.akamaihd.net`、`leagueoflegends.com` 等）落进 Global TV。两组默认都是 `Proxy`，默认设置下出口不变，但 Game Platform 切地区 / 直连时这些域名现在会跟着切
- Emby 服 `notnetflix.cos.cat` 新增内联规则，排在 `Netflix_Domain` 之前：此前被 `DOMAIN-KEYWORD,netflix` 先命中进 Netflix 组。不整体前移 `Emby_Domain`
- `docs/design-notes.md` 第三节补充上述三条硬性顺序依赖，⑩ 行按实际顺序改写

---

## 2026-09-24 — CI：固定运行环境（未升版本号，配置内容不变）

- `build-ini.yml` 的 `runs-on` 由 `ubuntu-latest` 固定为 `ubuntu-24.04`：`ubuntu-latest` 自 2026-10-19 起迁移到 Ubuntu 26，避免运行环境在没有改动的情况下变化（与 Openclash-Rule `46b5b50` 一致）

---

## 2026-09-24 — CI：与 Openclash-Rule 的双向通知（未升版本号，配置内容不变）

- `validate_ini.py` 新增 `--rule-ref <提交号>`：Openclash-Rule 的规则源改为按该提交从 raw 读取，报错注明「按 Rule 提交 xxxxxxx 校验」。收到 `rules-updated` 通知时传入通知里的提交号 —— 镜像约 5 分钟才同步，此前读镜像会漏过规则库刚删除或改名的文件
- 构建推送后若 `dist/Custom_Clash_V2.ini` 有变化，向 Openclash-Rule 发送 `config-updated`（携带推送后的 HEAD），触发对方的冗余分析。需配置 `RULE_DISPATCH_TOKEN`，未配置时跳过（见 [docs/操作流程.md](docs/操作流程.md) 第 7 节）
- 修正 `config-updated` 的触发条件：改为比较本次运行前后远端 main 上的 `dist/Custom_Clash_V2.ini`（push 以推送前的 tip 为基准，其他触发以 `GITHUB_SHA` 为基准），不再只看 bot 自己的提交。此前改规则顺序的推送（如 `9fa077f`、`18782dd`）自带 `dist/`，bot 只改 `manifest.json`，导致不会通知；bot 推送失败时不发送。推送重试中 rebase 冲突时改为中止并放弃
- jsdelivr 清缓存同样改为按远端 `dist/*.ini` 前后变化决定：此前只清 bot 提交里的文件，本地生成 `dist/` 一起推送时（如 `54baa87`）bot 无可提交，缓存不会被清。比对抽成独立步骤「比对远端 dist 变化」，清缓存与通知 Rule 共用

---

## 2026-09-24 — v1.x 旧配置维护（未升版本号）

- `cfg/Custom_Clash.ini` 注释掉已在规则库删除的 `BritboxUK_Domain` 引用（消除 404；其域名已由紧邻的 `UKMedia_Domain` 以同一 `UKNet` 分组覆盖，路由不变）
- 修正 `PH_Domain` 行首的 `:` 笔误为 `;` 注释（该行原本就不生效）
- 注释掉在规则库已为空的 `Steam_CDN_Domain`、`Supercell_Domain`、`Nintendo_IP` 引用（消除联网校验的空规则集告警；三者本就是 0 条规则，路由不变。V2 已于 2026-09-05/06 摘除）

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
