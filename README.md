# Accurate Clock Crafter 精准时钟合成器

An automation to make Minecraft resourcepacks of minute-level-accurate clock.  
能自动合成分钟级精确时钟的Minecraft资源包的脚本。
![demo](https://raw.githubusercontent.com/GrakePch/AccurateClockCrafter/master/images/demo.png)

## Usage & Requirements 用法与依赖

Only tested on Python 3.11+  

Library needed: **Pillow**  
To install, run ```pip install pillow``` in the terminal.  

Before running the script: 
- Put the texture file of clock face in **inputs/** and rename it to **bg.png**.
- Put the texture files of hour in **inputs/h/** and rename them to **0.png** to **23.png** (corresponding to 00:MM to 23:MM).
- Put the texture files of tens-digit of minute in **inputs/m1/** and rename them to **0.png** to **5.png** (corresponding to HH:0M to HH:5M).
- Put the texture files of ones-digit of minute in **inputs/m2/** and rename them to **0.png** to **9.png** (corresponding to HH:M0 to HH:M9).


Then, change the directory of the terminal to the root of this project (the same directory of file ACC.py) and run  
```
python .\ACC.py
```
Wait until the program completes, the generated files can be found in **outputs/**  

---

仅在Python 3.11以上版本测试过

需要库：**Pillow**  
如需安装，在终端运行 ```pip install pillow```

在运行脚本前：
- 将表盘贴图放在 **inputs/** 中，并且重命名为 **bg.png** 。
- 将小时贴图放在 **inputs/h/** 中，并且重命名为 **0.png** 至 **23.png**（分别对应 00:MM 至 23:MM）。
- 将分钟的十位数贴图放在 **inputs/m1/** 中，并且重命名为 **0.png** 至 **5.png**（分别对应 HH:0M 至 HH:5M）。
- 将分钟的个位数贴图放在 **inputs/m2/** 中，并且重命名为 **0.png** 至 **9.png**（分别对应 HH:M0 至 HH:M9）。

之后，将终端的路径改为本项目根目录（与ACC.py文件同一目录）并且运行
```
python .\ACC.py
```
等待程序完成，生成的文件将出现在 **outputs/** 中

## Templates 模板

There are several templates of inputs in **inputs_templates/**. Use the "inputs" folder under one of the templates to replace **inputs/** in the project root and run the script to get a usable resourcepack as references.

**inputs_templates/** 中有若干模板。将其中一个的 inputs 文件夹替换项目根目录的 **inputs/** 并且运行脚本以获得可用的资源包供参考。

## TODOs

- Support of making analog clock.
- Support of making PBR textures.
