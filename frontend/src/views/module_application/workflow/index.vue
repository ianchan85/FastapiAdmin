<template>
  <div class="app-container">
    <!-- 顶部操作栏 -->
    <div class="workflow-header">
      <h2>流程编排</h2>
      <div class="header-actions">
        <ElButton type="primary" @click="handleSave">保存流程</ElButton>
        <ElButton type="warning" @click="handleValidate">验证流程</ElButton>
        <ElButton @click="handleClear">清空画布</ElButton>
        <ElButton @click="handleLoadExample">加载示例</ElButton>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="workflow-main">
      <!-- 左侧节点库 -->
      <div class="node-library">
        <div class="node-library-title">节点库</div>
        <div class="node-library-search">
          <ElInput
            v-model="searchKeyword"
            placeholder="搜索节点"
            prefix-icon="el-icon-search"
            size="small"
            @input="handleSearch"
          />
        </div>
        <div id="dnd-panel" class="dnd-panel-container"></div>
      </div>

      <!-- 中央画布区域 -->
      <div class="canvas-wrapper">
        <div id="logicflow-canvas"></div>
      </div>

      <!-- 右侧属性面板 -->
      <div v-if="selectedNode" class="property-panel">
        <div class="property-panel-title">节点属性</div>
        <div class="property-panel-content">
          <ElForm :model="nodeProperties" label-width="80px">
            <ElFormItem label="节点名称">
              <ElInput v-model="nodeProperties.text" placeholder="请输入节点名称"></ElInput>
            </ElFormItem>
            <ElFormItem label="节点ID">
              <ElInput v-model="nodeProperties.id" disabled placeholder="节点ID"></ElInput>
            </ElFormItem>
            <ElFormItem label="节点类型">
              <ElInput v-model="nodeProperties.type" disabled placeholder="节点类型"></ElInput>
            </ElFormItem>
            <ElFormItem label="X坐标">
              <ElInputNumber v-model="nodeProperties.x" :min="0" :precision="0"></ElInputNumber>
            </ElFormItem>
            <ElFormItem label="Y坐标">
              <ElInputNumber v-model="nodeProperties.y" :min="0" :precision="0"></ElInputNumber>
            </ElFormItem>
            <ElFormItem>
              <ElButton type="primary" @click="saveNodeProperties">保存属性</ElButton>
              <ElButton @click="cancelEdit">取消</ElButton>
            </ElFormItem>
          </ElForm>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from "vue";
import LogicFlow from "@logicflow/core";
import { Control, Menu, DndPanel, SelectionSelect } from "@logicflow/extension";
import { ElMessage, ElForm, ElFormItem, ElInput, ElInputNumber, ElButton } from "element-plus";
import "@logicflow/core/lib/style/index.css";
import "@logicflow/extension/lib/style/index.css";

defineOptions({
  name: "Workflow",
  inheritAttrs: false,
});

//图方法
// 放大或缩小画布
// lf.zoom(isZoomIn);

// // 将图形移动到画布中心
// lf.focusOn(focusOnArgs);

// 监听事件
// lf.on(evt, callback);

// // 撤销
// lf.undo();

// // 获取画布数据
// lf.getGraphData();

// // 节点方法
// // 添加节点
// lf.addNode(nodeConfig);

// // 删除节点
// lf.deleteNode(nodeId);

// // 克隆节点
// lf.cloneNode(nodeId);

// // 获取节点的model数据
// lf.getNodeModel(nodeId);

// 连线方法
// 创建边
// lf.createEdge(edgeConfig);

// // 根据连线Id来删除边
// lf.deleteEdge(edgeId);

// // 根据连线两端节点的Id来删除边
// lf.removeEdge(sourceNodeId, targetNodeId);

// // 获取边的model数据
// lf.getEdge(config);

// // 获取边的数据属性
// lf.getEdgeData(edgeId);

// // 设置边的数据属性
// lf.setEdgeData(edgeAttribute);

// LogicFlow实例
let lf: LogicFlow | null = null;

// 选中的节点
const selectedNode = ref<any>(null);

// 节点属性
const nodeProperties = reactive({
  id: "",
  type: "",
  text: "",
  x: 0,
  y: 0,
});

// 搜索关键字
const searchKeyword = ref("");

// 搜索处理函数（暂时保留，可用于后续搜索功能扩展）
const handleSearch = () => {
  console.log("搜索节点:", searchKeyword.value);
};

// 节点类型定义可以在setPatternItems中配置

// 事件处理函数
const bindEvents = () => {
  if (!lf) return;

  // 节点添加事件
  lf.on("node:add", (params: any) => {
    console.log("节点添加:", params);
  });

  // DndPanel会自动处理拖拽事件，无需手动监听drop事件

  // 节点删除事件
  lf.on("node:remove", (params: any) => {
    console.log("节点删除:", params);
    if (selectedNode.value && selectedNode.value.id === params.data.id) {
      selectedNode.value = null;
    }
  });

  // 连线添加事件
  lf.on("edge:add", (params: any) => {
    console.log("连线添加:", params);
  });

  // 连线删除事件
  lf.on("edge:remove", (params: any) => {
    console.log("连线删除:", params);
  });

  // 节点选中事件
  lf.on("node:select", (params: any) => {
    console.log("节点选中:", params);
    selectedNode.value = params.data;
    // 填充属性表单
    nodeProperties.id = params.data.id;
    nodeProperties.type = params.data.type;
    nodeProperties.text = params.data.text || "";
    nodeProperties.x = params.data.x;
    nodeProperties.y = params.data.y;
  });

  // 连线选中事件
  lf.on("edge:select", (params: any) => {
    console.log("连线选中:", params);
    selectedNode.value = null; // 选中连线时隐藏属性面板
  });

  // 画布点击事件
  lf.on("canvas:click", (params: any) => {
    console.log("画布点击:", params);
    selectedNode.value = null; // 点击画布空白处隐藏属性面板
  });
};

// 保存节点属性
const saveNodeProperties = () => {
  if (!lf || !selectedNode.value) return;

  // 更新节点属性
  lf.updateNode({ ...nodeProperties });
  ElMessage.success("节点属性保存成功");
};

// 取消编辑
const cancelEdit = () => {
  if (selectedNode.value) {
    // 恢复原始属性
    nodeProperties.id = selectedNode.value.id;
    nodeProperties.type = selectedNode.value.type;
    nodeProperties.text = selectedNode.value.text || "";
    nodeProperties.x = selectedNode.value.x;
    nodeProperties.y = selectedNode.value.y;
  }
};

// 定义节点配置，接近参考demo的实现方式
const nodeConfigs = {
  startNode: {
    extendsNode: "rect",
    getShape() {
      return {
        type: "rect",
        attr: {
          width: 80,
          height: 40,
          fill: "#e6f7ff",
          stroke: "#1890ff",
          radius: 20,
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#1890ff",
      };
    },
  },
  endNode: {
    extendsNode: "rect",
    getShape() {
      return {
        type: "rect",
        attr: {
          width: 80,
          height: 40,
          fill: "#fff2f0",
          stroke: "#ff4d4f",
          radius: 20,
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#ff4d4f",
      };
    },
  },
  taskNode: {
    extendsNode: "rect",
    getShape() {
      return {
        type: "rect",
        attr: {
          width: 100,
          height: 60,
          fill: "#ffffff",
          stroke: "#1890ff",
          radius: 4,
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#333333",
      };
    },
  },
  conditionNode: {
    extendsNode: "diamond",
    getShape() {
      return {
        type: "diamond",
        attr: {
          width: 80,
          height: 80,
          fill: "#fffbe6",
          stroke: "#faad14",
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#333333",
      };
    },
  },
  approvalNode: {
    extendsNode: "rect",
    getShape() {
      return {
        type: "rect",
        attr: {
          width: 100,
          height: 60,
          fill: "#f6ffed",
          stroke: "#722ed1",
          radius: 4,
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#333333",
      };
    },
  },
  parallelNode: {
    extendsNode: "rect",
    getShape() {
      return {
        type: "rect",
        attr: {
          width: 100,
          height: 60,
          fill: "#e6fffb",
          stroke: "#13c2c2",
          radius: 4,
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#333333",
      };
    },
  },
  subprocessNode: {
    extendsNode: "rect",
    getShape() {
      return {
        type: "rect",
        attr: {
          width: 100,
          height: 60,
          fill: "#fff0f6",
          stroke: "#eb2f96",
          radius: 4,
          strokeDasharray: "5,5",
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#333333",
      };
    },
  },
  timerNode: {
    extendsNode: "circle",
    getShape() {
      return {
        type: "circle",
        attr: {
          r: 30,
          fill: "#fff7e6",
          stroke: "#fa8c16",
        },
      };
    },
    getTextStyle() {
      return {
        fontSize: 14,
        fill: "#333333",
      };
    },
  },
};

// 注册自定义节点，参考demo的实现方式
const registerCustomNodes = () => {
  if (!lf) return;

  // 注册所有节点配置
  Object.entries(nodeConfigs).forEach(([type, config]) => {
    lf.register(type, config);
  });
};

// 功能按钮处理函数
const handleSave = () => {
  if (!lf) return;
  const graphData = lf.getGraphData();
  console.log("保存流程数据:", graphData);
  ElMessage.success("流程保存成功");
};

const handleValidate = () => {
  if (!lf) return;
  const graphData = lf.getGraphData();
  const { nodes, edges } = graphData;
  const errors: string[] = [];

  // 检查开始节点
  const startNodes = nodes.filter((node) => node.type === "startNode");
  if (startNodes.length === 0) {
    errors.push("流程缺少开始节点");
  } else if (startNodes.length > 1) {
    errors.push("流程只能有一个开始节点");
  }

  // 检查结束节点
  const endNodes = nodes.filter((node) => node.type === "endNode");
  if (endNodes.length === 0) {
    errors.push("流程缺少结束节点");
  } else if (endNodes.length > 1) {
    errors.push("流程只能有一个结束节点");
  }

  // 检查孤立节点
  const nodeIds = new Set(nodes.map((node) => node.id));
  const connectedNodeIds = new Set<string>();

  edges.forEach((edge) => {
    connectedNodeIds.add(edge.sourceNodeId);
    connectedNodeIds.add(edge.targetNodeId);
  });

  nodeIds.forEach((nodeId) => {
    if (!connectedNodeIds.has(nodeId)) {
      const node = nodes.find((n) => n.id === nodeId);
      if (node) {
        errors.push(`节点 "${node.text || node.id}" 是孤立节点，没有任何连线`);
      }
    }
  });

  // 检查结束节点是否有出边
  endNodes.forEach((endNode) => {
    const endNodeEdges = edges.filter((edge) => edge.sourceNodeId === endNode.id);
    if (endNodeEdges.length > 0) {
      errors.push(`结束节点 "${endNode.text || endNode.id}" 不能有出边`);
    }
  });

  // 检查开始节点是否有入边
  startNodes.forEach((startNode) => {
    const startNodeEdges = edges.filter((edge) => edge.targetNodeId === startNode.id);
    if (startNodeEdges.length > 0) {
      errors.push(`开始节点 "${startNode.text || startNode.id}" 不能有入边`);
    }
  });

  // 检查循环路径
  const hasCycle = checkCycle(nodes, edges);
  if (hasCycle) {
    errors.push("流程中存在循环路径");
  }

  // 显示验证结果
  if (errors.length > 0) {
    ElMessage.error({
      message: `流程验证失败，发现 ${errors.length} 个问题：\n${errors.join("\n")}`,
      duration: 5000,
      showClose: true,
    });
  } else {
    ElMessage.success("流程验证通过！");
  }
};

// 检查是否有循环路径
const checkCycle = (nodes: any[], edges: any[]) => {
  const nodeMap = new Map(nodes.map((node) => [node.id, []]));
  const visited = new Set<string>();
  const recStack = new Set<string>();

  // 构建邻接表
  edges.forEach((edge) => {
    const neighbors = nodeMap.get(edge.sourceNodeId) || [];
    neighbors.push(edge.targetNodeId);
    nodeMap.set(edge.sourceNodeId, neighbors);
  });

  // DFS 检测循环
  const dfs = (nodeId: string): boolean => {
    if (!visited.has(nodeId)) {
      visited.add(nodeId);
      recStack.add(nodeId);

      const neighbors = nodeMap.get(nodeId) || [];
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor) && dfs(neighbor)) {
          return true;
        } else if (recStack.has(neighbor)) {
          return true;
        }
      }
    }
    recStack.delete(nodeId);
    return false;
  };

  // 对每个未访问的节点执行 DFS
  for (const node of nodes) {
    if (dfs(node.id)) {
      return true;
    }
  }

  return false;
};

const handleClear = () => {
  if (!lf) return;
  lf.clear();
  ElMessage.info("画布已清空");
};

const handleLoadExample = () => {
  if (!lf) return;
  const exampleData = {
    nodes: [
      {
        id: "start1",
        type: "startNode",
        x: 200,
        y: 100,
        text: "开始",
      },
      {
        id: "task1",
        type: "taskNode",
        x: 200,
        y: 200,
        text: "任务1",
      },
      {
        id: "condition1",
        type: "conditionNode",
        x: 200,
        y: 300,
        text: "条件",
      },
      {
        id: "approval1",
        type: "approvalNode",
        x: 100,
        y: 400,
        text: "审批",
      },
      {
        id: "task2",
        type: "taskNode",
        x: 300,
        y: 400,
        text: "任务2",
      },
      {
        id: "end1",
        type: "endNode",
        x: 200,
        y: 500,
        text: "结束",
      },
    ],
    edges: [
      {
        id: "edge1",
        sourceNodeId: "start1",
        targetNodeId: "task1",
      },
      {
        id: "edge2",
        sourceNodeId: "task1",
        targetNodeId: "condition1",
      },
      {
        id: "edge3",
        sourceNodeId: "condition1",
        targetNodeId: "approval1",
        text: "是",
      },
      {
        id: "edge4",
        sourceNodeId: "condition1",
        targetNodeId: "task2",
        text: "否",
      },
      {
        id: "edge5",
        sourceNodeId: "approval1",
        targetNodeId: "end1",
      },
      {
        id: "edge6",
        sourceNodeId: "task2",
        targetNodeId: "end1",
      },
    ],
  };
  lf.render(exampleData);
  ElMessage.success("示例流程加载成功");
};

// 窗口大小变化处理
const handleResize = () => {
  if (lf) {
    lf.resize(window.innerWidth - 350 - 300, window.innerHeight - 100);
  }
};

// 初始化LogicFlow
const initLogicFlow = () => {
  if (lf) return;

  lf = new LogicFlow({
    container: document.querySelector("#logicflow-canvas"),
    // 画布配置
    width: window.innerWidth - 350 - 300,
    height: window.innerHeight - 100,
    background: {
      color: "#F0F0F0",
    },
    grid: {
      type: "dot",
      size: 20,
    },
    snapline: true,
    textEdit: true,
    isSilentMode: false,
    edgeType: "line",
    keyboard: {
      enabled: true,
    },
    plugins: [Control, Menu, SelectionSelect],
  });

  // 注册自定义节点
  registerCustomNodes();

  // 增强节点和连线的视觉效果
  enhanceVisuals();

  // 绑定事件
  bindEvents();

  // 使用DndPanel的setPatternItems方法配置节点面板
  lf.extension.dndPanel.setPatternItems([
    { type: "startNode", label: "开始节点" },
    { type: "endNode", label: "结束节点" },
    { type: "taskNode", label: "任务节点" },
    { type: "conditionNode", label: "条件节点" },
    { type: "approvalNode", label: "审批节点" },
    { type: "parallelNode", label: "并行节点" },
    { type: "subprocessNode", label: "子流程节点" },
    { type: "timerNode", label: "定时节点" },
  ]);

  // 渲染 - 提供空的图数据
  lf.render({ nodes: [], edges: [] });
};

// 增强节点和连线的视觉效果
const enhanceVisuals = () => {
  if (!lf) return;

  // 为节点添加鼠标悬停效果
  lf.on("node:mouseenter", (params) => {
    const node = params.data;
    lf?.setNodeStyle(node.id, {
      boxShadow: "0 0 10px rgba(0, 0, 0, 0.3)",
      transition: "all 0.3s ease",
      scale: 1.05,
    });
  });

  lf.on("node:mouseleave", (params) => {
    const node = params.data;
    lf?.setNodeStyle(node.id, {
      boxShadow: "none",
      transition: "all 0.3s ease",
      scale: 1,
    });
  });

  // 节点选中效果
  lf.on("node:select", (params) => {
    const node = params.data;
    lf?.setNodeStyle(node.id, {
      strokeWidth: 3,
      boxShadow: "0 0 15px rgba(24, 144, 255, 0.5)",
    });
  });

  // 节点取消选中效果
  lf.on("node:unselect", (params) => {
    const node = params.data;
    lf?.setNodeStyle(node.id, {
      strokeWidth: 2,
      boxShadow: "none",
    });
  });

  // 连线样式增强
  lf.on("edge:select", (params) => {
    const edge = params.data;
    lf?.setEdgeStyle(edge.id, {
      strokeWidth: 3,
      stroke: "#1890ff",
    });
  });

  lf.on("edge:unselect", (params) => {
    const edge = params.data;
    lf?.setEdgeStyle(edge.id, {
      strokeWidth: 2,
      stroke: "#aaa",
    });
  });

  // 连线鼠标悬停效果
  lf.on("edge:mouseenter", (params) => {
    const edge = params.data;
    lf?.setEdgeStyle(edge.id, {
      strokeWidth: 3,
      stroke: "#1890ff",
    });
  });

  lf.on("edge:mouseleave", (params) => {
    const edge = params.data;
    lf?.setEdgeStyle(edge.id, {
      strokeWidth: 2,
      stroke: edge.selected ? "#1890ff" : "#aaa",
    });
  });
};

// 生命周期钩子
onMounted(() => {
  initLogicFlow();
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  if (lf) {
    lf.destroy();
    lf = null;
  }
  window.removeEventListener("resize", handleResize);
});
</script>

<style lang="scss" scoped>
.app-container {
  .workflow-header {
    height: 60px;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .workflow-main {
    flex: 1;
    display: flex;
    overflow: hidden;

    .node-library {
      width: 350px;
      display: flex;
      flex-direction: column;

      .node-library-title {
        height: 40px;
        line-height: 40px;
        padding: 0 20px;
        font-size: 16px;
        font-weight: 500;
      }

      .node-library-search {
        padding: 12px 20px;
      }

      #dnd-panel {
        flex: 1;
        padding: 16px;
        overflow-y: auto;

        .dnd-node-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          margin-bottom: 8px;
          border-radius: 6px;
          cursor: move;
          transition: all 0.3s ease;
          background-color: #ffffff;
          border: 1px solid #e0e0e0;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

          &:hover {
            background-color: #f0f9ff;
            border-color: #91d5ff;
            box-shadow: 0 4px 8px rgba(24, 144, 255, 0.15);
          }
        }
      }
    }

    .canvas-wrapper {
      flex: 1;
      position: relative;

      #logicflow-canvas {
        width: 100%;
        height: 100%;
      }
    }

    .property-panel {
      width: 300px;
      display: flex;
      flex-direction: column;

      .property-panel-title {
        height: 40px;
        line-height: 40px;
        padding: 0 20px;
        font-size: 16px;
        font-weight: 500;
      }

      .property-panel-content {
        flex: 1;
        padding: 20px;
        overflow-y: auto;

        :deep(.el-form-item) {
          margin-bottom: 20px;
        }

        :deep(.el-form-item__label) {
          font-weight: 500;
        }
      }
    }
  }
}
</style>
