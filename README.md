# PlanTimer

基于 PyQt6 的 Windows 桌面定时任务管理器。

## 功能

- 可视化创建/编辑/删除定时任务
- 支持指定星期、时间自动执行程序或脚本
- 任务执行前弹窗提醒，支持自定义系统提示音
- 系统托盘常驻
- 数据 JSON 持久化

## 使用

```bash
pip install PyQt6
python PlanTimer/main.py
```

## 项目结构

```
PlanTimer/
├── main.py              # 主程序
├── data/
│   ├── settings.json    # 应用设置
│   └── tasks.json       # 任务数据
└── README.md
```
