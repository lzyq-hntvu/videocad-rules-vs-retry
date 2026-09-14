# Day1 连通与下载验证日志（VideoCAD）

## 已完成

1. 创建目录结构
- `evidence/videocad/notes`
- `evidence/videocad/samples`
- `evidence/videocad/scripts`
- `evidence/videocad/logs`

2. 保存来源页面（本地）
- `notes/sources/videocad_project_page.html`
- `notes/sources/VideoCAD_README.md`
- `notes/sources/harvard_dataverse_metadata.json`

3. 最小样本下载验证（成功）
- `samples/dataverse/readme.md`（1.3KB）
- `samples/dataverse/qa.json`（约5.0MB）

## 阻塞/异常

1. `harvard_dataverse_page.html`（Dataverse 页面 HTML）抓取结果为空
- 处理策略：改用 Dataverse API 元数据接口（已成功）

## Day2 建议起点

1. 下载 `action_json.zip`（约23MB）
2. 解压并查看 JSON 字段结构
3. 输出字段说明与一个最小解析脚本

