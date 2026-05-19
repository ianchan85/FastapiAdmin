<template>
  <div class="workplace-container">
    <!-- 电商模块 -->
    <div class="card-group">
      <ElRow :gutter="24">
        <ElCol :sm="12" :md="12" :lg="6"><TotalOrderVolume /></ElCol>
        <ElCol :sm="12" :md="12" :lg="6"><TotalProducts /></ElCol>
        <ElCol :sm="24" :md="12" :lg="6"><ProductSales /></ElCol>
        <ElCol :sm="24" :md="12" :lg="6"><SalesGrowth /></ElCol>
      </ElRow>

      <ElRow :gutter="24">
        <ElCol :span="24"><CartConversionRate /></ElCol>
      </ElRow>

      <ElRow :gutter="24">
        <ElCol :sm="12" :md="12" :lg="6"><SalesTrend /></ElCol>
        <ElCol :sm="12" :md="12" :lg="6"><SalesClassification /></ElCol>
        <ElCol :sm="24" :md="12" :lg="6"><HotCommodity /></ElCol>
        <ElCol :sm="24" :md="12" :lg="6"><AnnualSales /></ElCol>
      </ElRow>
    </div>

    <!-- 用户分析 -->
    <div class="card-group">
      <ElRow :gutter="24">
        <ElCol :sm="24" :md="12" :lg="12" class="mb-5"><ActiveUser /></ElCol>
        <ElCol :sm="24" :md="12" :lg="12" class="mb-5"><SalesOverview /></ElCol>
        <ElCol
          v-for="card in statsCards"
          :key="`t-${card.id}`"
          :xs="24"
          :sm="12"
          :md="6"
          class="mb-5"
        >
          <FaStatsCard
            :icon="card.icon"
            :iconStyle="card.iconStyle"
            :title="card.title"
            :description="card.description"
            :showArrow="card.showArrow"
          />
        </ElCol>
        <ElCol
          v-for="card in statsCards"
          :key="`n-${card.id}`"
          :xs="24"
          :sm="12"
          :md="6"
          class="mb-5"
        >
          <FaStatsCard
            :icon="card.icon"
            :iconStyle="card.iconStyle"
            :title="card.title"
            :description="card.description"
            :count="card.count"
            :decimals="0"
            :showArrow="card.showArrow"
            separator=","
          />
        </ElCol>
        <ElCol
          v-for="card in statsCards"
          :key="`c-${card.id}`"
          :xs="24"
          :sm="12"
          :md="6"
          class="mb-5"
        >
          <FaStatsCard
            :icon="card.icon"
            :iconStyle="card.customIconStyle"
            :boxStyle="card.boxStyle"
            :title="card.title"
            :description="card.description"
            :textColor="card.textColor"
            :showArrow="card.showArrow"
          />
        </ElCol>
        <ElCol
          v-for="card in progressCards"
          :key="`p-${card.id}`"
          :xs="24"
          :sm="12"
          :md="6"
          class="mb-5"
        >
          <FaProgressCard :percentage="card.percentage" :title="card.title" :color="card.color" />
        </ElCol>
        <ElCol
          v-for="card in progressCards"
          :key="`pi-${card.id}`"
          :xs="24"
          :sm="12"
          :md="6"
          class="mb-5"
        >
          <FaProgressCard
            :percentage="card.percentage"
            :title="card.title"
            :color="card.color"
            :icon="card.icon"
            :iconStyle="card.iconStyle"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaLineChartCard
            :isMiniChart="true"
            :value="2545"
            label="新用户"
            date="过去7天"
            :percentage="1.2"
            :height="9.5"
            :chartData="[120, 132, 101, 134, 90, 230, 210]"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaBarChartCard
            :isMiniChart="true"
            :value="15480"
            label="浏览量"
            date="过去14天"
            :percentage="-4.15"
            :height="9.5"
            barWidth="45%"
            :chartData="[120, 100, 150, 140, 90, 120, 130]"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaLineChartCard
            :isMiniChart="true"
            :value="2545"
            label="粉丝数"
            date="过去30天"
            :percentage="1.2"
            :height="9.5"
            :showAreaColor="true"
            :chartData="[150, 180, 160, 200, 180, 220, 240]"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaDonutChartCard
            :value="36358"
            title="粉丝量"
            :percentage="18"
            percentageLabel="较去年"
            :data="[50, 40]"
            :height="9.5"
            currentValue="2022"
            previousValue="2021"
            :radius="['50%', '70%']"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaLineChartCard
            :value="2545"
            label="新用户"
            :percentage="1.2"
            :height="11"
            :chartData="[120, 132, 101, 134, 90, 230, 210]"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaBarChartCard
            :value="15480"
            label="浏览量"
            :percentage="-4.15"
            :height="11"
            :chartData="[120, 100, 150, 140, 90, 120, 130, 110]"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaLineChartCard
            :value="2545"
            label="粉丝数"
            :percentage="1.2"
            :height="11"
            :showAreaColor="true"
            :chartData="[150, 180, 160, 200, 180, 220, 240]"
          />
        </ElCol>
        <ElCol :xs="24" :sm="12" :md="6" class="mb-5">
          <FaDonutChartCard
            :value="36358"
            title="粉丝量"
            :percentage="-18"
            percentageLabel="较2021年"
            :data="[70, 30]"
            :height="11"
            currentValue="12月"
            previousValue="11月"
          />
        </ElCol>
      </ElRow>
    </div>
  </div>
</template>

<script setup lang="ts">
import ActiveUser from "./modules/active-user.vue";
import SalesOverview from "./modules/sales-overview.vue";
import TotalOrderVolume from "./modules/total-order-volume.vue";
import TotalProducts from "./modules/total-products.vue";
import SalesTrend from "./modules/sales-trend.vue";
import SalesClassification from "./modules/sales-classification.vue";
import HotCommodity from "./modules/hot-commodity.vue";
import AnnualSales from "./modules/annual-sales.vue";
import ProductSales from "./modules/product-sales.vue";
import SalesGrowth from "./modules/sales-growth.vue";
import CartConversionRate from "./modules/cart-conversion-rate.vue";
import FaLineChartCard from "@/components/cards/fa-line-chart-card/index.vue";
import FaStatsCard from "@/components/cards/fa-stats-card/index.vue";
import FaProgressCard from "@/components/cards/fa-progress-card/index.vue";
import FaBarChartCard from "@/components/cards/fa-bar-chart-card/index.vue";
import FaDonutChartCard from "@/components/cards/fa-donut-chart-card/index.vue";

defineOptions({ name: "DashboardWorkplace" });

const statsCards = [
  {
    id: 1,
    title: "销售产品",
    count: 1235,
    description: "鞋子、牛仔裤、派对服装、手表",
    icon: "ri:bar-chart-box-line",
    boxStyle: "bg-theme/10!",
    customIconStyle: "text-theme! text-3xl!",
    iconStyle: "bg-info",
    textColor: "var(--theme-color)",
    showArrow: false,
  },
  {
    id: 2,
    title: "活跃用户",
    count: 5000,
    description: "日活跃用户超过5,000+",
    icon: "ri:account-box-2-line",
    boxStyle: "bg-warning/10!",
    customIconStyle: "text-warning! text-3xl!",
    iconStyle: "bg-warning",
    textColor: "var(--fa-warning)",
    showArrow: false,
  },
  {
    id: 3,
    title: "总收入",
    count: 35000,
    description: "月收入超过¥350,000+",
    icon: "ri:money-cny-box-line",
    boxStyle: "bg-secondary/10!",
    customIconStyle: "text-secondary! text-3xl!",
    iconStyle: "bg-secondary",
    textColor: "var(--fa-secondary)",
    showArrow: false,
  },
  {
    id: 4,
    title: "客户评价",
    count: 4800,
    description: "平均评分4.8/5",
    icon: "ri:message-3-line",
    boxStyle: "bg-error/10!",
    customIconStyle: "text-error! text-3xl!",
    iconStyle: "bg-error",
    textColor: "var(--fa-error)",
    showArrow: false,
  },
];
const progressCards = [
  {
    id: 1,
    title: "完成进度",
    percentage: 75,
    color: "var(--fa-success)",
    icon: "ri:arrow-up-circle-line",
    iconStyle: "bg-success/12 text-success",
  },
  {
    id: 2,
    title: "项目进度",
    percentage: 65,
    color: "var(--theme-color)",
    icon: "ri:twitch-line",
    iconStyle: "bg-theme/12 text-theme",
  },
  {
    id: 3,
    title: "学习进度",
    percentage: 45,
    color: "var(--fa-error)",
    icon: "ri:game-line",
    iconStyle: "bg-error/12! text-error",
  },
  {
    id: 4,
    title: "任务进度",
    percentage: 90,
    color: "var(--fa-secondary)",
    icon: "ri:flag-2-line",
    iconStyle: "bg-secondary/12 text-secondary",
  },
];
</script>

<style scoped>
@reference "@styles/core/tailwind.css";

:deep(.el-card) {
  --el-card-border-radius: calc(var(--custom-radius) + 2px);

  border: 1px solid var(--fa-card-border);
}

.workplace-container {
  display: flex;
  flex-direction: column;

  > * {
    margin-bottom: 16px;
  }

  > :last-child {
    margin-bottom: 0;
  }

  &::after {
    display: block;
    flex-shrink: 0;
    height: 16px;
    content: "";
  }
}

.card-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-row {
  row-gap: 16px;
}
</style>
