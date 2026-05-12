# Gov RAG Frontend

React + Tailwind + shadcn 风格组件前端。

## 启动

前提：

- 后端 API 已经启动在 `http://127.0.0.1:8081`
- 本机可用 `python`
- `dist` 已经构建完成

前台启动：

```powershell
cd E:\code\gov-rag\frontend
.\start.ps1
```

后台启动：

```powershell
cd E:\code\gov-rag\frontend
.\start-hidden.ps1
```

如果端口冲突，可以指定端口：

```powershell
.\start.ps1 -Port 5174
```

## 访问

默认访问地址：

`http://127.0.0.1:5173`

如果你改了前端代码，需要重新构建：

```powershell
cd E:\code\gov-rag\frontend
npm run build
```

## 当前页面功能

- 查看已接入数据源
- 触发杭州数据采集
- 搜索已入库文档
- 提问并查看带引用回答

## 技术说明

- 使用 Vite + React + TypeScript
- 使用 Tailwind CSS v4
- 使用一组本地实现的 shadcn 风格基础组件
- 页面默认直接请求 `http://127.0.0.1:8081`
