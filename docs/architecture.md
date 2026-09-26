# 架构说明

本文件描述策略组的分层方式与地区意图。规则顺序、命名等约定见 [design-notes.md](design-notes.md)。

---

## 一、三层架构

```
Layer 0  节点池（url-test，正则匹配机场节点名）
         🇭🇰 HK Node / 🇯🇵 JP Node / 🇸🇬 SG Node / 🇺🇸 US Node
         🇬🇧 UK Node / 🇩🇪 DE Node / 🇦🇺 AU Node / 🇧🇷 BR Node
         ↑ 唯一跟机场节点名打交道的一层。机场全量改名时只需要改这一层的正则

Layer 1  地区锚点（select，第一候选 = 对应节点池，末尾带 .*）
         Proxy(HK) / USNet / JPNet / SGNet / UKNet / EUNet / AUNet / BRNet
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
| `Proxy` | 🇭🇰 HK | 香港，通用与低延迟场景；主流流媒体（Netflix / Disney+ / HBO）、社交、开发、游戏平台的默认出口 |
| `USNet` | 🇺🇸 US | 美国，AI 与美区专属服务（Hulu / PrimeVideo / Spotify / TikTok / X / 购物）；美国本土金融与 VoIP |
| `SGNet` | 🇸🇬 SG | 新加坡，亚洲金融分流中心，亚洲虚拟币业务平台基本都走这里 |
| `JPNet` | 🇯🇵 JP | 日本本地服务，以及 YouTube / Emby / 即时通讯的默认出口；**没有专用节点的地区统一挂靠这里**（如菲律宾，内容已并入 `JP_Domain`） |
| `UKNet` | 🇬🇧 UK | 英国，**只放本地服务**（银行、Britbox、UK 媒体），不承担通用代理 |
| `EUNet` | 🇩🇪 DE | 欧洲 |
| `AUNet` | 🇦🇺 AU | 大洋洲 |
| `BRNet` | 🇧🇷 BR | 南美 |

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
| Netflix / Disney+ / HBO / Apple TV+ / Global TV | `Proxy` | 港区内容库，低延迟 |
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
| Self-Hosted / Custom-Made | `Global Direct` | 默认直连，被墙时面板切代理 |

---

## 五、为什么不用单候选组

「平台组只放一个节点组」在技术上可行 —— subconverter 的 `groupGenerate()` 对 `[]组名` 是原样插入不做校验，生成的配置不会为空。但代价不对等：

| 目标 | 靠什么实现 | 单候选是必需的吗 |
|---|---|---|
| 新安装不用手选 | 第一候选正确 | 否 |
| 机场改名后不崩 | 候选是组名而非节点名 | 否 |
| 防止误操作切错 | 单候选 | 是 |

前两个才是实际痛点，靠「第一候选 = 意图锚点」就全解决。单候选只多带来防误操作，代价是节点全挂时无法手动救急，而且降级是静默的（见 troubleshooting 第四节）。
