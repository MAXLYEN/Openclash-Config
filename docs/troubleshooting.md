# 排查记录

踩过的坑、原因、以及怎么验证。约定见 [design-notes.md](design-notes.md)。

---

## 一、provider 静默失效（规则数为 0）

**现象**：provider 加载成功，但规则完全不生效，流量落到 GeoSite 兜底。

**原因**：`ruleset=` 带了更新间隔就会生成 rule-provider，而 Clash 的 `classical` behavior provider 要求 payload 是 YAML 数组：

```yaml
payload:
  - DOMAIN-SUFFIX,claude.ai
  - DOMAIN-KEYWORD,anthropic
```

纯文本 `.list`（每行一条、无 `payload:` 键）解析不出任何内容。缺 `clash-classic:` 前缀、或用了 `clash-domain:` 而内容是 classical 格式，都会得到同样的结果。

**为什么长期没发现**：兜底大多也能把流量导向正确的分组。访问 `claude.ai` 时日志显示 `match GeoSite(category-ai-!cn) using Optional` 而不是 `RuleSet(Claude_Domain)`，行为看起来正常。核对后确认 166 个 provider 全部未生效。

**排查**：

```bash
# 看 provider 缓存是不是空的
ls -la /etc/openclash/rule_provider/

# 日志里命中的是 RuleSet( 还是 GeoSite(
grep -E "RuleSet\(|GeoSite\(" /tmp/openclash.log | tail -50
```

**已固化的防线**：`scripts/validate_ini.py --online` 会拉取每个规则源的前 4KB，检查是否含 `payload:`，不含则报 ERROR。

---

## 二、策略组选择丢失

OpenClash 在 `yml_change.sh:532` 无条件写入：

```ruby
(Value['profile'] ||= {})['store-selected'] = true
```

选择记录存在 `/etc/openclash/history/${配置文件名}.db`。启动时 `init.d/openclash` 先 `rm -rf /etc/openclash/cache.db`，再把它软链回 history 里那个 db。

所以：

| 操作 | 选择是否保留 |
|---|---|
| 重启 | 保留 |
| 订阅更新 | 保留 |
| **换配置文件名** | **丢失** —— history 按配置文件名隔离 |
| **策略组改名** | **丢失** —— 该组记录失效 |
| **机场改了节点名** | **丢失** —— 记录里的目标不存在 |

最后一条最容易中招：手选的是**具体节点名**时，机场一次改名就全崩；选的是 url-test **组名**（`🇭🇰 HK Node`）时，组名由本仓库定义，机场怎么改都不影响。

这是三层架构里「平台组只引用锚点组、锚点组只引用节点池」的主要动机之一。

丢失后所有 select 组回落到第一候选 —— 所以第一候选必须是意图节点，见 [architecture.md](architecture.md) 第三节。

---

## 三、正则误匹配

历史案例：

| 正则 | 误匹配 |
|---|---|
| `AU` | `AUTO`（Auto-Test 被塞进澳洲组） |
| `GB` | `100GB`（流量标注被当成英国节点） |
| `新` | `新北`（台湾节点被当成新加坡） |

修法：字母缩写统一写作 `\bXX[-_ ]?\d*\b`，中文关键词避免用单字。

**Go RE2 不支持 `(?!...)` 和 `(?<!...)`**，用负向断言排除会导致正则编译失败、分组静默变空，且没有任何报错。`validate_ini.py` 会拦下这类语法。

---

## 四、单候选组静默降级为直连

url-test 组的正则匹配不到任何节点时，subconverter 会插入 `DIRECT`：

```cpp
if(filtered_nodelist.empty())
    filtered_nodelist.emplace_back("DIRECT");
```

于是 `UKNet` → `🇬🇧 UK Node` → `DIRECT`。**不报错，但英国本地服务（银行、Britbox）会裸连**，面板上还显示正常。

这是 fail-open 不是 fail-closed。所以锚点组末尾保留 `.*`、平台组保留多个候选，节点全挂时至少能手动救急。

`validate_ini.py` 对只有一个候选的分组会报 WARN（内建的 `Global Direct` / `Global Reject` 除外）。

---

## 五、地区规则集吃掉平台组

**现象**：面板上切 ChatGPT 组的节点，对 `chatgpt.com` 不生效。

**原因**：`US_Domain` 排在第 15 位，而 `OpenAI_Domain` 在第 45 位。`US_Domain` 里的 `DOMAIN-KEYWORD,chatgpt` 先命中，流量进了 `Optional`（现 `USNet`），永远到不了 ChatGPT 组。

同类问题：

| 域名 | 曾经命中 | 应该命中 |
|---|---|---|
| `chatgpt.com` | `US_Domain` → Optional | `OpenAI_Domain` → ChatGPT |
| `copilot.microsoft.com` | `US_Domain` → Optional | `Copilot_Domain` → Copilot |
| `amazon.co.uk` | `UKNet_Domain`(`co.uk`) → UKNet | `Amazon_Domain` → Shopping Platform |
| `shopee.com.sg` | `SG_Domain`(`com.sg`) → Cryptocurrency | `Shopee_Domain` → Shopping Platform |
| `www.gstatic.com` | `Gemini_Domain` → Optional | `Google_Domain` → Google |
| `crypto.com` | `UKNet_Domain`(`DOMAIN-KEYWORD,crypto`) → UKNet | Cryptocurrency |

**根因**：ccTLD 兜底（`co.uk` / `com.sg`）和通用关键词混在地区文件里，而地区文件排在平台之前。修法是地区文件整体下沉，见 [design-notes.md](design-notes.md) 第三节。

---

## 六、改完顺序后的验证清单

OpenClash 日志搜 `RuleSet(`，逐条核对：

| 域名 | 期望命中 | 期望分组 |
|---|---|---|
| `chatgpt.com` | `RuleSet(OpenAI_Domain)` | ChatGPT |
| `copilot.microsoft.com` | `RuleSet(Copilot_Domain)` | Copilot |
| `amazon.co.uk` | `RuleSet(Amazon_Domain)` | Shopping Platform |
| `shopee.com.sg` | `RuleSet(Shopee_Domain)` | Shopping Platform |
| `www.gstatic.com` | 内联规则 | Google |
| `crypto.com` | 内联规则 | Cryptocurrency |
| `www.dbs.com.sg` | `RuleSet(SG_Domain)` | SGNet |
| `store.steampowered.com` | `RuleSet(Steam_Domain)` | Steam |

面板确认：换一个配置文件名强制丢弃 history 后，`Proxy` 显示香港节点、`USNet` 显示美国节点、`Cryptocurrency` 显示新加坡节点、`UKNet` 显示英国节点。

---

## 七、Fake-IP 模式下 IP 规则很少命中

境外域名在 Fake-IP 模式下解析成 `198.18.x.x`，不会命中 IP 区；只有国内域名返回真实 IP 时才可能命中。所以 IP 规则的作用主要在直连 IP 的场景（部分 App、P2P、某些客户端）。

判断某条 IP 规则是否真的需要维护时，先想清楚它要覆盖的是不是这类场景。绝大多数平台的 `_IP` 规则可以由 `[]GEOIP,xxx` 兜底，不必手工维护。
