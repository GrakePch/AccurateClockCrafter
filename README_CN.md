# 精准时钟合成器
 
能自动合成分钟级精确时钟的Minecraft资源包的脚本。
![demo](https://raw.githubusercontent.com/GrakePch/AccurateClockCrafter/master/images/styles_1.1.png)

## 用法与依赖

仅在Python 3.11以上版本测试过

需要库：**Pillow**  
如需安装，在终端运行 ```pip install pillow```

## 项目结构

- `main.py`：顶层入口（运行 `python main.py`）。
- `accurate_clock_crafter/main.py`：编排入口（可运行 `python -m accurate_clock_crafter.main`）。
- `accurate_clock_crafter/builders/`：指针与数位时钟构建器。
- `accurate_clock_crafter/core/`：时间曲线、模型分发、pack 元数据策略。
- `accurate_clock_crafter/io/`：模板读取与资源包写盘。
- `accurate_clock_crafter/utils/`：命名、数学、图像工具函数。


在运行脚本前：
- 将 pack.mcmeta 文件放在 **inputs/[your_pack_name]/** 中。
- 将表盘贴图放在 **inputs/[your_pack_name]/** 中，并且重命名为 **bg.png** 。
- 将小时贴图放在 **inputs/[your_pack_name]/h/** 中，并且重命名为 **0.png** 至 **23.png**（分别对应 00:MM 至 23:MM）。
- 如果制作数位时钟
    - 将分钟的十位数贴图放在 **inputs/[your_pack_name]/m1/** 中，并且重命名为 **0.png** 至 **5.png**（分别对应 HH:0M 至 HH:5M）。
    - 将分钟的个位数贴图放在 **inputs/[your_pack_name]/m2/** 中，并且重命名为 **0.png** 至 **9.png**（分别对应 HH:M0 至 HH:M9）。
- 如果制作指针时钟
    - 在 pack.mcmeta 中， 在根`{}`中添加如下代码结构：
    ```json
    "acc_config": {
        "mode": "a",
        "is_hour_higher": true
    }
    ```
    - 将分针贴图放在 **inputs/[your_pack_name]/m/** 中，并且将他们重命名为各自代表的分钟时刻。（例如，代表 HH:05 的分针应当命名为 05.png 或 5.png）

之后，将终端路径切换到本项目根目录并运行
```
python .\main.py
```
等待程序完成，生成的文件将出现在 **outputs/** 中（单包输出）：
- `Analog_Clock`
- `Giant_Analog_Clock`
- `Square_Analog_Clock`
- `Square_Digital_Clock`
- `AccurateClocks`

### 在 pack.mcmeta 中自定义配置
配置选项代码 `"acc_config": {...}` 将不会出现在导出的 pack.mcmeta 中。
```json
{
  "pack": {
    "description": "[your description]"
  },
  "acc_config": {
    "mode": "d",
    "is_hour_higher": false,
    "pack_icon_time": [9, 30]
  }
}

```
- `"mode":`
    - `"d"`: 数位时钟 (默认)
    - `"a"`: 指针时钟
- `"is_hour_higher":`
    - `false`: 时针的图层低于分针 (默认)
    - `true`: 时针的图层高于分针
- `"pack_icon_time": [HH, MM]`
    - 使用 HHMM 时刻的贴图作为 pack.png（默认值为 [9, 30]）

## 模板

**inputs_templates/** 中有若干模板，脚本会直接从该目录读取并在 **outputs/** 生成对应资源包。

## TODOs

- [x] Support of making analog clock.
- [x] Support of making OptiFine emissive textures.
- [ ] Support of making PBR textures.
