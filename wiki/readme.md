[项目主页](https://github.com/Eason3Blue/CiweimaoDownloader)

# 软件介绍
本软件只能够下载免费章节和已购买的章节。

# 本软件优点
1. 下载在手机端进行，软件无需登录，不接触账号相关数据。
2. 自动生成全文txt、epub以及单章txt，且自动解析文章中的图片url后整合到epub中，且位置不变。
3. 程序生成epub符合其3.3版本的规范。
4. 程序使用结构体Chapters和Book传递参数，简洁易读。
5. 程序使用了多线程特性，处理速度快。

# 教程
## 一.准备下载工具
1. 一个安卓模拟器，要求可以**开启root权限**，本文以MuMu模拟器为例。
2. 一个文件管理器，要求可以使用root权限访问根目录，本文以MT文件管理器为例
3. 刺猬猫app，要求版本大于2.9.303。
4. 解码软件，前往[下载页面](https://github.com/Eason3Blue/CiweimaoDownloader/releases/latest)下载，下载完后请解压压缩包

## 二、安装环境

1. 安装MuMu模拟器，并安装MT文件管理器和刺猬猫小说app（如果是第二次使用，请先清空刺猬猫小说app的应用数据或重装）开启模拟器root权限<img src="\img\CiweimaoDownloader\1.png" alt="开启root权限的选项" />

## 三、模拟器下载

2. 打开刺猬猫app，正常登录，找到你想下载的小说，用鼠标左键长按它，选择"下载所有章节"<img src="\img\CiweimaoDownloader\2.png" alt="选择下载所有章节" />

3. 等待下载完成，完成后再等至少一分钟，期间不要操作模拟器，也不要用其他手机登录刺猬猫。等完后，关闭刺猬猫app

4. 打开MT文件管理器，弹出权限申请，全部选择允许

5. 右侧操作面板点击`$MuMu12Shared`，左侧面板点击最上面的`..`直到没有`..`为止<img src="\img\CiweimaoDownloader\3.png" alt="文件导航" />

6. 在左边面板依次找到 `data/data/com.kuangxiangciweimao.novel/files`，之后在分别找到 `Y2hlcy8` 文件夹和 `novelCiwei/reader/booksnew/<小说数字id>`，分别长按它们选择`复制->`，选择确认复制。<img src="\img\CiweimaoDownloader\4.png" alt="文件操作对话框" />

## 四、导出关键数据

7. 点击模拟器上面的那个箭头，选择`文件传输`<img src="\img\CiweimaoDownloader\5.png" alt="文件传输工具" />

8. 选择上栏右侧的"打开"<img src="\img\CiweimaoDownloader\6.png" alt="文件传输工具" />弹出了一个文件夹，选中`Y2hlcy8`和`<小说数字id>`两个文件夹，复制到一个纯英文目录，例如`D:\cwmd`

## 五、运行程序解码

9. 将下载解码软件也解压到`D:\cwmd`，将`Y2hlcy8`改名成`key`<img src="\img\CiweimaoDownloader\7.png" alt="目录样貌" />

10. 双击运行main.exe，等待程序输出到
```
[OPT] 输入你想下载的书籍Url或目录名字：
```
<img src="\img\CiweimaoDownloader\8.png" alt="控制台" />如果你操作规范，这里只检测出一个，那么直接复制输出的`<小说数字id>`并粘贴到输入中即可

11. 如果你有多个，那么打开浏览器，进入ciweimao.com，搜索找到你要的小说，把它的url粘贴下来<img src="\img\CiweimaoDownloader\9.png" alt="小说主页" />

12. 等待程序运行成功，若出现问题，请前往[Issues页面](https://github.com/Eason3Blue/CiweimaoDownloader/issues)提出问题，你应该能在文件夹中找到小说对应的txt和epub文件

# 做出贡献
如果你在使用过程中遇到了bug，或者你有什么新奇的想法，或者你想要什么功能，都请前往[Issues页面](https://github.com/Eason3Blue/CiweimaoDownloader/issues)，若此项目帮到了你，请前往[项目主页](https://github.com/Eason3Blue/CiweimaoDownloader)上点个**Star**吧


# 版权说明
📖 仅供个人学习与技术研究

⛔ 禁止任何形式的商业用途

©️ 所有内容版权归原作者及刺猬猫平台所有

⏰ 请在 24 小时内学习后立即删除文件

⚠️ 作者不承担因不当使用导致的损失及法律后果