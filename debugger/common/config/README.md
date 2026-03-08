# Platform Adapter Config 
 
本目录保存 framework 到 RenderDoc/RDC platform tools 的共享接入真相。 
 
模板化后的约束： 
 
- `debugger/common/` 是唯一长期维护的共享来源。 
- `debugger/platforms/*` 只保留宿主模板，不再复制 `common/docs/scripts`。 
- 平台模板里的 hooks/skills/agents 只能引导宿主读取将来被用户拷入平台根的 `common/`。 
- 平台 tools 的真实路径、catalog、MCP/CLI 启动命令仍属于 adapter/config 层，不是 framework 真相。 
 
当前文件： 
 
- `platform_capabilities.json`：记录宿主能力与模板最小必需入口。 
- `platform_adapter.json`：记录共享 adapter 默认值，由宿主薄包装在运行时读取或引用。 
- `model_routing.json`：角色到模型偏好的 SSOT。 
 
不允许在平台模板里再维护第二份共享正文或第二份路径真相。
