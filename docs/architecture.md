# 架构说明

本文件描述策略组的分层方式与地区意图。规则顺序、命名等约定见 [design-notes.md](design-notes.md)。

---

## 一、三层架构

```
Layer 0  节点池（url-test，正则匹配机场节点名）
         🇭🇰 HK Node / 🇯🇵 JP Node / 🇸🇬 SG Node / 🇺🇸 US Node
         🇬🇧 UK Node / 🇩🇪 DE Node / 🇦🇺 AU Node / 🇧🇷 BR Node
         🇺🇸 US Alt（fallback：RackNerd 优先，不可用时退回 🇺🇸 US Node）
         ↑ 唯一跟机场节点名打交道的一层。机场全量改名时只需要改这一层的正则

Layer 1  地区锚点（select，第一候选 = 对应节点池，末尾带 .*）
         Proxy(HK) / USNet / JPNet / SGNet / UKNet / EUNet / AUNet / BRNet
         USAlt（美国备用出口，见第六节）
         ↑ 常驻节点组，也是没有专用节点的地区的挂靠落点

Layer 2  平台组（select，候选 = 锚点组，第一个 = 该平台默认地区）
         Netflix / ChatGPT / Cryptocurrency / Steam / GitHub / ...
         ↑ 只表达「这个平台默认走哪个地区」，不碰具体节点
```

好处：

- 改一个地区的出口只需要动 Layer 1 的一个组，所有引用它的平台组同步生效
- 加一个新地区只需要加一个节点池 + 一个锚点
- 平台组的候选只含锚点组（3~10 项），不再直接列节点池与 `.*`

约束：

- **锚点之间不互相引用**。Clash 加载时会检测策略组循环引用并直接失败，`validate_ini.py` 里有对应的 DFS 检查
- 锚点组末尾保留 `.*`，需要钉死某个具体节点（流媒体解锁）时在锚点层改一次即可

---

## 二、地区意图

| 锚点 | 节点池 | 承载内容 |
|---|---|---|
| `Proxy` | 🇭🇰 HK | 香港，通用与低延迟场景；主流流媒体（Disney+ / HBO）、社交、开发、游戏平台的默认出口 |
| `USNet` | 🇺🇸 US | 美国，AI 与美区专属服务（Hulu / PrimeVideo / Spotify / TikTok / X / 购物）；美国本土金融与 VoIP |
| `SGNet` | 🇸🇬 SG | 新加坡，亚洲金融分流中心，亚洲虚拟币业务平台基本都走这里 |
| `JPNet` | 🇯🇵 JP | 日本本地服务与日本 Hulu，以及 Netflix（含 `fast.com`）/ YouTube / Emby / 即时通讯的默认出口；**没有专用节点的地区统一挂靠这里**（如菲律宾，内容已并入 `JP_Domain`） |
| `UKNet` | 🇬🇧 UK | 英国，**只放本地服务**（银行、Britbox、UK 媒体），不承担通用代理 |
| `EUNet` | 🇩🇪 DE | 欧洲 |
| `AUNet` | 🇦🇺 AU | 大洋洲 |
| `BRNet` | 🇧🇷 BR | 南美 |
| `USAlt` | 🇺🇸 US Alt | 美国备用出口：只给常用美国节点被平台降级的服务用（首批 Meta AI），日常美国流量仍走 `USNet` |

`Proxy` 保留原名而没有改成 `HKNet`，因为它同时承担「通用代理入口」的角色，很多平台组的第二候选指向它。

---

## 三、为什么锚点的第一候选必须正确

Clash 的 `select` 组在没有选择记录时使用**第一个候选**。改造前的默认值全是错的：

| 组 | 改造前第一候选 | 实际默认行为 |
|---|---|---|
| Proxy | `Auto-Test` | 全球最低延迟节点，不是香港 |
| Optional | `Global Direct` | 直连 —— US_Domain / Claude / Gemini / Nvidia 全部裸连 |
| Cryptocurrency | `Proxy` | → Auto-Test，不是新加坡 |
| EUNet / UKNet | `Proxy` | → Auto-Test，不是德国 / 英国 |

也就是说全新安装时地区映射一条都不生效。之所以长期没暴露，是因为选择记录一直在。选择记录的丢失条件见 [troubleshooting.md](troubleshooting.md) 第二节。

---

## 四、平台组的默认锚点

| 平台组 | 第一候选 | 依据 |
|---|---|---|
| Disney+ / HBO / Apple TV+ / Global TV | `Proxy` | 港区内容库，低延迟 |
| Netflix | `JPNet` | 默认日本；域名、IP 与 GEOSITE / GEOIP 兜底均归 Netflix 组，保留其他地区候选 |
| Hulu / PrimeVideo / Spotify | `USNet` | 美区专属服务 |
| Emby | `JPNet` | Emby 服务器在日本 |
| YouTube / Instant Messaging | `JPNet` | 日本节点 |
| ChatGPT / Copilot | `USNet` | 美国承载 AI（候选不含 `Proxy`，香港不在服务区） |
| TikTok / Twitter(X) / Snapchat / Shopping Platform | `USNet` | 美区服务 |
| Talkatone / Paypal | `USNet` | 仅美 / 英 / 欧候选 |
| Cryptocurrency / Google / Google FCM | `SGNet` | 新加坡是亚洲金融分流中心 |
| Bahamut | `Proxy` | 台湾站，港节点最近 |
| Telegram / Social Media | `Proxy` | 延迟优先；Meta 域名与 IP 由更早的 USNet 规则处理 |
| GitHub / Microsoft / Apple / Speedtest | `Proxy` | 延迟优先 |
| Game Platform / Steam | `Proxy` | 第二候选 `Global Direct` |
| UnpopularNet / Others | `Proxy` | `Others` 即 `[]FINAL` 兜底 |
| PT | `Global Direct` | PT 必须走本地出口 |
| Netease / Xiaomi / Domestic TV | `Global Direct` | 国区服务 |
| Self-Hosted | `Global Direct` | 默认直连，被墙时面板切代理 |
| Custom-Made | `Global Direct` | 默认直连；被墙或直连太慢时面板切代理（如 EA 下载 CDN `origin-a.akamaihd.net`） |

`fast.com` 由前置的 Netflix 域名规则命中，跟随 Netflix 组选择，默认 `JPNet`。日本 Hulu 的 `HuluJP_Domain` 直接归 `JPNet`；美国 Hulu 走 Hulu 平台组，默认 `USNet`。第一候选只决定无选择记录时的默认值；已有 Netflix 选择记录的用户需在面板切到 `JPNet`。

---

## 五、为什么不用单候选组

「平台组只放一个节点组」在技术上可行 —— subconverter 的 `groupGenerate()` 对 `[]组名` 是原样插入不做校验，生成的配置不会为空。但代价不对等：

| 目标 | 靠什么实现 | 单候选是必需的吗 |
|---|---|---|
| 新安装不用手选 | 第一候选正确 | 否 |
| 机场改名后不崩 | 候选是组名而非节点名 | 否 |
| 防止误操作切错 | 单候选 | 是 |

前两个才是实际痛点，靠「第一候选 = 意图锚点」就全解决。单候选只多带来防误操作，代价是节点全挂时无法手动救急，而且降级是静默的（见 troubleshooting 第四节）。

---

## 六、出口覆盖：USAlt 与家宽（未启用）

有些平台的问题不在「该走哪个地区」，而在「这个地区的常用节点它不认」。这类需求按**出口要求**归类，不按平台建组：一份规则名单对应一个出口，名单排在 ③ 区末尾，早于所有平台规则与地区规则，命中即走该出口。

### USAlt：美国备用出口（2026-10-06 启用）

| 项 | 内容 |
|---|---|
| 起因 | 常用美国节点（AS2914 NTT 段）被 Meta 降级：同一个 Key 调 `api.meta.ai/v1/models` 只返回 1 个模型，`dev.meta.ai` 登录后跳 `/unavailable?reason=geo`；RackNerd 节点（AS36352）返回全部 8 个模型、网页可正常使用。两者 ipinfo 都是美国洛杉矶，差别在 IP 类型 / 信誉而不是地区 |
| 节点池 | `🇺🇸 US Alt`，`fallback` 类型：正则 `RackNerd` 在前，`[]🇺🇸 US Node` 在后。RackNerd 不可用时自动退回常用美国池（Meta 只是模型变少，不会断网），也保证该组永不为空，不会被 subconverter 塞 `DIRECT` |
| 锚点 | `USAlt`，写法与其他锚点一致：第一候选 `🇺🇸 US Alt`，末尾 `.*` |
| 规则 | Openclash-Rule 的 `USAlt_Domain`（首批：`DOMAIN-SUFFIX,meta.ai`、`DOMAIN,auth.meta.com`、`DOMAIN,accountscenter.meta.com`）与 `USAlt_IP`（空占位） |
| 日常流量 | 不受影响，美国流量仍走 `USNet` |

以后其他平台遇到同样问题（常用美国节点被降级），把它的域名加进 `USAlt_Domain` 即可，Config 不用改。登录会跳到 `www.facebook.com`，它仍走 `USNet`（常用节点）。2026-10-06 实测：USNet 切回常用节点、只有 Meta AI 走 RackNerd 时，`dev.meta.ai` 可正常登录，因此 `www.facebook.com` 不需要放进 `USAlt_Domain`。

### 家宽专用（Residential，未启用）

为「只能走真家宽」的平台准备，配置已写进 `cfg/Custom_Clash_V2.ini`（Layer 0 末尾「家宽方案」段，以及 ③ 区末尾、IP 区里对应的 `Residential` 行），整段注释，构建产物不受影响。要点：

- 家宽节点按订阅来源区分：订阅地址写成 `机场订阅|tag:家宽,家宽链接`，家宽池用 `!!GROUP=家宽` 取节点，机场池加 `!!GROUPID=0!!` 只取第 1 个订阅，避免日常流量消耗按量计费的家宽
- 8 个国家各一个 `🏠 XX Home` 池，末尾带 `[]REJECT`；`Residential` 组只放家宽池加 `REJECT`，不放机场锚点和 `Global Direct`。家宽不可用时宁可断网，也不换出口
- 家宽名单排在 USAlt 之前，优先级最高
- 买家宽前先查 ASN：应为 Comcast / Charter / Verizon / AT&T 等家庭宽带；NTT、Cogent 等骨干网转租的「ISP 住宅」与常用美国节点是同一类，会被同样降级

启用步骤写在 ini 里那段注释的开头。
