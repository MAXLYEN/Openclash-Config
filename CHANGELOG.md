# 更新记录

本模板引用的规则碎片来自 [Openclash-Rule](https://github.com/MAXLYEN/Openclash-Rule)，规则内容的更新与本模板的更新没有直接关系。

设计约定与架构说明不在本文件，见 [docs/design-notes.md](docs/design-notes.md) 与 [docs/architecture.md](docs/architecture.md)。

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
