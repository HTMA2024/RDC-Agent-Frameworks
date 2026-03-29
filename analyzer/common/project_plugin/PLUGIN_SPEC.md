# Project Plugin Specification

## 用途

Project Plugin 允许为特定项目/引擎提供渲染管线结构和命名规范，辅助 analyzer 的模块识别和 Pass 功能映射。

## 格式

```yaml
project: "MyGame"
engine: "Unity HDRP"
api: "Vulkan"

pass_naming_conventions:
  - pattern: "ShadowPass*"
    stage: "预处理/深度"
    module: "shadow"
  - pattern: "GBuffer*"
    stage: "GBuffer/几何"
    module: "geometry"
  - pattern: "DeferredLighting*"
    stage: "光照/着色"
    module: "lighting"

known_modules:
  - name: water
    typical_passes: ["WaterCompute", "WaterForward"]
  - name: post_process
    typical_passes: ["Bloom*", "ToneMap*", "FXAA*"]

material_system:
  block_fingerprints:
    - name: "LIGHTING_BLOCK"
      pattern: "NdotL * lightColor"
    - name: "PBR_BLOCK"
      pattern: "GGX * F * G / (4 * NdotV * NdotL)"
```

## 使用方式

将项目特定的 YAML 文件放入 `common/project_plugin/` 目录。
`pipeline_overview` 和 `technique_analyst` agent 会在运行时加载匹配的 plugin。
