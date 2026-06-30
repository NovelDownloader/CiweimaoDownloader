# CiweimaoDownloader

抢救导出已官方下架的书籍，预先导出可能下架的书籍。本软件不是也不支持破解，不能下载没有购买的章节


## 本软件优点
1. 支持 ADB 自动拉取，连接模拟器/手机后一键完成，无需手动操作文件。
2. 支持官方已下架书籍的抢救性导出
3. 下载在手机端进行，软件无需登录。
4. 自动生成全文txt、epub以及单章txt，且自动解析文章中的图片url后整合到epub中，且位置不变。
5. 程序生成epub符合其3.3版本的规范。
6. 程序使用结构体，简洁易读。
7. 程序使用了多线程和异步特性，处理速度快。


温馨提示：本软件仅为了个人存档、学习使用，想要传播盗版、损坏原作者利益的请自觉离开

## 运行方式

- **Windows**: 解压后双击 `run.bat`
- **Linux**: 解压后运行 `./run.sh`

无需安装 Python，运行`run.bat`或`run.sh`即可。ADB 工具也已内置在 `adb/` 目录中。

## 使用教程

详见[使用说明](https://github.com/NovelDownloader/CiweimaoDownloader/blob/main/wiki/readme.md)和压缩包内 `使用说明.md`

## 构建

```bash
# Windows (PowerShell)
.\build.ps1

# Linux
./build.sh
```

构建产物位于 `build/` 目录。

## 开发

```bash
pip install -r requirements.txt
python src/main.py
```

## 版权声明

本软件基于 **GPL-3.0** 协议开源。

* 📖 **仅供个人学习与技术研究**  
* ⛔ **禁止任何形式的商业用途**  
* ©️ 所有内容版权归**原作者及刺猬猫平台**所有  
* ⏰ 请在 **24 小时内**学习后立即删除文件  
* ⚠️ 作者**不承担**因不当使用导致的损失及法律后果  

> 使用本软件即表示您同意上述条款
