# Gov RAG

面向全国政务公开网站的知识库与问答系统骨架。

这个第一版不是按“杭州特例”写死，而是按“多站点、多栏目、可配置抓取、可追溯问答”来设计。

## 第一版目标

- 支持登记多个政务站点来源
- 支持基于配置的栏目抓取规则
- 支持把网页正文、发布时间、来源、附件等入库
- 提供基础搜索接口
- 提供问答接口骨架，回答时返回引用来源

## 当前包含

- FastAPI 服务骨架
- SQLAlchemy 数据模型
- 站点配置加载
- 通用政务站点抓取器骨架
- 文档搜索与问答接口
- 杭州政府站点示例配置
- 浏览器请求头与常见政务详情页正文抽取启发式规则
- 已验证的杭州通知公告采集、入库、检索、问答最小链路

## 目录结构

```text
gov-rag/
  app/
    api/
    crawlers/
    services/
    sources/
  README.md
  pyproject.toml
  .env.example
```

## 运行方式

1. 安装依赖

```powershell
cd C:\Users\Administrator\Desktop\gov-rag
python -m pip install -e .
```

2. 配置环境变量

```powershell
Copy-Item .env.example .env
```

3. 启动服务

```powershell
.\start.ps1
```

如果要后台启动：

```powershell
.\start-hidden.ps1
```

如果 `8080` 被占用，可以指定端口：

```powershell
.\start.ps1 -Port 8081
.\start-hidden.ps1 -Port 8081
```

4. 访问接口文档

`http://127.0.0.1:8080/docs`

## 当前接口

- `GET /health`
- `GET /sources`
- `POST /sources/reload`
- `GET /documents/search?q=关键词`
- `POST /ingest/run`
- `POST /ask`

## 已验证示例

当前已经验证以下最小链路可用：

1. 从杭州站点示例配置加载数据源
2. 抓取杭州通知公告列表中的详情页
3. 抽取标题、发布时间、来源、正文并入库
4. 通过检索接口和问答服务返回带来源的结果

注意：

- 现在的问答仍是“检索汇总式回答”，还没有接入真实大模型
- 全国政务站点并不能靠一个抓取规则全部覆盖，后续需要继续补站点配置和专用适配器
- 当前默认数据库是本地 SQLite，适合开发验证，不适合正式生产
- Windows 下不要使用 `uvicorn --reload`，当前环境会触发权限错误并导致服务异常

## 下一步建议

1. 增加 PostgreSQL + pgvector 正式存储
2. 把通用抓取器补成站点适配器体系
3. 增加 PDF/附件抽取
4. 接入真实模型和 embedding
5. 增加增量调度与失败重试
6. 做前端搜索和问答页

## 关于全国站点

全国政务站点无法依靠单一规则全覆盖，正确做法是：

- 有一层通用抓取能力
- 有一层站点配置
- 对结构差异大的站点补专用适配器

这个工程骨架就是按这个思路搭的。
