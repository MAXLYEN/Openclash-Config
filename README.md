# Openclash-Config

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build config](https://github.com/MAXLYEN/Openclash-Config/actions/workflows/build-ini.yml/badge.svg)](https://github.com/MAXLYEN/Openclash-Config/actions/workflows/build-ini.yml)

OpenClash 订阅转换用的**外部配置模板**（subconverter `&config=` 参数指向的文件），采用三层策略组架构，规则来自 [Openclash-Rule](https://github.com/MAXLYEN/Openclash-Rule)。

> 注意：这不是 OpenClash 的 `config.yaml`。本仓库提供的是订阅转换阶段的外部配置，由 subconverter 读取后生成最终的 Clash 配置。

---

## 下载地址

正式使用请引用 `dist/` 下的产物（零注释版本）：

```
https://raw.githubusercontent.com/MAXLYEN/Openclash-Config/main/dist/Custom_Clash_V2.ini
```

jsdelivr 镜像：

```
https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Config@main/dist/Custom_Clash_V2.ini
```

填入 OpenClash → 配置订阅 → 订阅转换 → 自定义配置文件地址。作为 `&config=` 参数手动拼 URL 时需要先做 URLEncode。

`cfg/Custom_Clash.ini` 是旧版模板，仅为兼容既有订阅链接保留，不再维护，新配置请用 V2。

---

## 目录结构

| 目录       | 说明                                               |
| ---------- | -------------------------------------------------- |
| `cfg/`     | 配置源文件，**手动维护**，带完整注释，是唯一数据源 |
| `dist/`    | 构建产物，**自动生成**，零注释，正式引用地址       |
| `docs/`    | 设计约定、架构说明与排查记录                       |
| `scripts/` | 构建与校验脚本                                     |

`cfg/` 与 `dist/` 的关系等同于 [Openclash-Rule](https://github.com/MAXLYEN/Openclash-Rule) 里 `rules/list/` 与 `rules/yaml/` 的关系：前者人写，后者机器生成，**不要直接编辑 `dist/`**。

---

## 三层策略组架构

```
Layer 0  节点池（url-test）    🇭🇰 🇯🇵 🇸🇬 🇺🇸 🇬🇧 🇩🇪 🇦🇺 🇧🇷
                                唯一跟机场节点名打交道的一层

Layer 1  地区锚点（select）    Proxy(HK) USNet JPNet SGNet UKNet EUNet AUNet BRNet
                                第一候选恒为对应节点池，全新配置无需手选

Layer 2  平台组（select）      Netflix / ChatGPT / Cryptocurrency / Steam / ...
                                候选只放锚点组，第一个 = 该平台默认地区
```

改一个地区的出口只需要动 Layer 1 的一个组；机场节点全部改名时只需要改 Layer 0 的正则。

地区意图：

| 锚点              | 承载内容                                 |
| ----------------- | ---------------------------------------- |
| `Proxy`           | 香港，通用与低延迟场景                   |
| `USNet`           | 美国，流媒体与 AI                        |
| `SGNet`           | 新加坡，亚洲金融与虚拟币                 |
| `JPNet`           | 日本，含无专用节点地区的挂靠（如菲律宾） |
| `UKNet`           | 英国，仅本地服务                         |
| `EUNet`           | 欧洲                                     |
| `AUNet` / `BRNet` | 大洋洲 / 南美                            |

详见 [docs/architecture.md](docs/architecture.md)。

---

## 本地构建

```bash
python3 scripts/validate_ini.py            # 结构校验
python3 scripts/build_ini.py               # 生成 dist/
python3 scripts/validate_ini.py --online   # 拉取所有规则源，校验 provider 结构
```

`cfg/` 有变化时 GitHub Actions 会自动跑上述流程并提交 `dist/`。

---

## 文档

- [设计约定](docs/design-notes.md) —— 规则源分档、分组归属、检索顺序、subconverter 行为约定
- [架构说明](docs/architecture.md) —— 三层架构、锚点默认值、地区意图
- [排查记录](docs/troubleshooting.md) —— 踩过的坑与验证方法
- [更新记录](CHANGELOG.md)

---

## 相关项目

- [Openclash-Rule](https://github.com/MAXLYEN/Openclash-Rule) —— 本模板引用的分流规则库
- [vernesong/OpenClash](https://github.com/vernesong/OpenClash) —— OpenClash 本体
- [tindy2013/subconverter](https://github.com/tindy2013/subconverter) —— 订阅转换后端
- [Aethersailor/SubConverter-Extended](https://github.com/Aethersailor/SubConverter-Extended) —— 增强版订阅转换后端

---

## 致谢

本项目最初基于 [Aethersailor/Custom_OpenClash_Rules](https://github.com/Aethersailor/Custom_OpenClash_Rules) 的订阅转换模板定制，其 OpenClash 设置教程与模板结构为本项目提供了最初的思路。

当前版本的配置模板、策略组架构与分流规则均已完全重写，与上游不存在代码级关联，本仓库亦不是上游的 fork。上游项目的使用问题请前往其自身仓库反馈。

感谢：

- [Aethersailor](https://github.com/Aethersailor) —— 订阅转换模板与 OpenClash 设置教程
- [vernesong](https://github.com/vernesong) —— OpenClash
- [tindy2013](https://github.com/tindy2013) —— subconverter
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) —— 部分规则碎片来源

---

## 许可证

[MIT](LICENSE)
